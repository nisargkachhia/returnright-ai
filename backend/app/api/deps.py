"""FastAPI dependencies."""

from fastapi import Header, HTTPException

from app.config import get_settings


def current_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    settings = get_settings()
    user_id = (x_user_id or settings.demo_user_id).strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="X-User-Id required")
    return user_id
