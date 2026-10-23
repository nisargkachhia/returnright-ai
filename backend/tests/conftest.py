"""Pytest fixtures with isolated SQLite DB."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Isolate settings before application imports
_TEST_DB = Path(__file__).resolve().parent / "_test_returnright.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ["DEMO_MODE"] = "true"
os.environ["DEMO_USER_ID"] = "demo-user-1"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from app.config import get_settings

get_settings.cache_clear()

from app.db import session as db_session
from app.db.migrate import apply_schema
from app.db.seed import reset_and_seed
from app.domain.models import Base
from app.main import create_app
from app.mcp import server as mcp_server


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=db_session.engine)
    apply_schema(db_session.engine)
    session = db_session.SessionLocal()
    reset_and_seed(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    # Reset MCP singleton so tools bind cleanly per test session
    mcp_server._mcp = None
    app = create_app()
    app.dependency_overrides[db_session.get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clean_db_file():
    yield
    # keep file for inspection on failure; recreate each db fixture
