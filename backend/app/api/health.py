"""Health endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.migrate import schema_version
from app.db.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        app_env=settings.app_env.value,
        demo_mode=settings.demo_mode,
        policy_as_of=settings.policy_as_of.isoformat(),
        schema_version=schema_version(db),
        mcp_endpoint="/mcp",
    )
