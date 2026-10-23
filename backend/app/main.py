"""FastAPI host: REST API + official MCP Streamable HTTP at /mcp."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, health, orders, policies, policy
from app.config import get_settings
from app.db.session import init_db
from app.logging_config import configure_logging, get_logger
from app.mcp.server import create_mcp_server, get_mcp_asgi_app

configure_logging()
logger = get_logger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", env=settings.app_env, demo_mode=settings.demo_mode)
    init_db(seed=True)
    mcp = create_mcp_server()
    # Mounted sub-app lifespans do not run — host must start the session manager.
    async with mcp.session_manager.run():
        logger.info("mcp_session_manager_started")
        try:
            yield
        finally:
            logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        description=(
            "ReturnRight AI demo backend. REST under /api/v1; "
            "MCP Streamable HTTP under /mcp. Synthetic data only."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-User-Id",
            "Last-Event-ID",
            "Mcp-Method",
            "Mcp-Name",
            "Mcp-Protocol-Version",
            "Mcp-Session-Id",
        ],
        expose_headers=["Mcp-Session-Id"],
    )

    app.include_router(health.router)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(orders.router, prefix="/api/v1")
    app.include_router(policies.router, prefix="/api/v1")
    app.include_router(policy.router, prefix="/api/v1")
    app.include_router(cases.router, prefix="/api/v1")

    # Official MCP Streamable HTTP endpoint: /mcp
    app.mount("/mcp", get_mcp_asgi_app())
    return app


app = create_app()
