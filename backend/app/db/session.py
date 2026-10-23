"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.migrate import apply_schema, enable_sqlite_foreign_keys

_settings = get_settings()
connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
engine = create_engine(_settings.database_url, future=True, connect_args=connect_args)
enable_sqlite_foreign_keys(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(*, seed: bool = True) -> None:
    """Create or migrate the schema, then optionally load synthetic demo data."""
    if _settings.database_url.startswith("sqlite:///"):
        raw = _settings.database_url.removeprefix("sqlite:///")
        if raw not in {":memory:", ""} and not raw.startswith("file:"):
            Path(raw).expanduser().parent.mkdir(parents=True, exist_ok=True)

    apply_schema(engine)
    if seed:
        from app.db.seed import seed_demo_data

        with SessionLocal() as db:
            seed_demo_data(db)
