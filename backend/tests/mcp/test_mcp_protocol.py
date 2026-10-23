"""MCP Streamable HTTP protocol tests (initialize, tools/list, tools/call)."""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import httpx
import pytest
import uvicorn

from app.main import create_app


def _mcp_headers(session_id: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-11-25",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    return headers


def _post_mcp(base: str, payload: dict[str, Any], session_id: str | None = None) -> httpx.Response:
    # Trailing slash avoids Starlette Mount 307 redirects that drop POST bodies.
    return httpx.post(
        f"{base}/mcp/",
        headers=_mcp_headers(session_id),
        json=payload,
        timeout=30.0,
        follow_redirects=False,
    )


@pytest.fixture(scope="module")
def mcp_base_url(tmp_path_factory):
    """Run the FastAPI+MCP app on a local port for real HTTP protocol tests."""
    db_path = tmp_path_factory.mktemp("mcp") / "mcp.db"
    import os

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["DEMO_MODE"] = "true"
    from app.config import get_settings
    from app.db import session as db_session
    from app.mcp import server as mcp_server

    get_settings.cache_clear()
    # Rebuild engine against temp DB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{db_path}", future=True, connect_args={"check_same_thread": False})
    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    mcp_server._mcp = None
    db_session.init_db(seed=True)

    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base = "http://127.0.0.1:8765"
    for _ in range(50):
        try:
            r = httpx.get(f"{base}/health", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        pytest.fail("MCP test server failed to start")

    yield base
    server.should_exit = True
    thread.join(timeout=5)


def test_mcp_initialize_list_and_call(mcp_base_url):
    init = _post_mcp(
        mcp_base_url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "returnright-tests", "version": "0.1.0"},
            },
        },
    )
    assert init.status_code in (200, 202), init.text
    session_id = init.headers.get("mcp-session-id")
    body = init.json()
    # JSON response mode returns a single JSON-RPC object
    if isinstance(body, dict) and "result" in body:
        result = body["result"]
    else:
        # Some responses may wrap differently; be explicit about failure
        pytest.fail(f"Unexpected initialize payload: {body}")

    assert "protocolVersion" in result
    assert result["protocolVersion"] >= "2025-03-26"
    assert "capabilities" in result
    assert result["serverInfo"]["name"]

    # notifications/initialized (no response required)
    _post_mcp(
        mcp_base_url,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session_id,
    )

    listed = _post_mcp(
        mcp_base_url,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        session_id=session_id,
    )
    assert listed.status_code == 200, listed.text
    tools = listed.json()["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "search_orders" in names
    assert "evaluate_policy" in names
    assert "confirm_resolution_action" in names

    called = _post_mcp(
        mcp_base_url,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_orders",
                "arguments": {"query": "headphones", "user_id": "demo-user-1"},
            },
        },
        session_id=session_id,
    )
    assert called.status_code == 200, called.text
    content = called.json()["result"]["content"]
    assert content
    text = content[0].get("text", "")
    payload = json.loads(text)
    assert payload.get("error") is None, payload
    assert payload["data_provenance"] == "demo"
    assert len(payload["results"]) >= 1
    assert any(r["id"] == "ord-headphones" for r in payload["results"])
