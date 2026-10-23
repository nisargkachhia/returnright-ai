"""Versioned SQLite schema initialization and additive migrations."""

from __future__ import annotations

from sqlalchemy import Engine, event, inspect, text
from sqlalchemy.orm import Session

from app.domain.models import Base, SchemaMeta

SCHEMA_VERSION = "2"

_ADDITIVE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "merchant_policies": [
        ("effective_to", "DATETIME"),
        ("is_hypothetical", "BOOLEAN DEFAULT 1"),
        ("disclaimer", "TEXT DEFAULT 'HYPOTHETICAL DEMO POLICY — not an actual retailer policy.'"),
    ],
    "policy_rules": [
        ("rule_kind", "VARCHAR(32) DEFAULT 'return_window'"),
    ],
    "resolution_actions": [
        ("decided_at", "DATETIME"),
        ("result_note", "TEXT"),
        ("result_recorded_at", "DATETIME"),
    ],
    "follow_up_tasks": [
        ("completed_at", "DATETIME"),
    ],
}


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    def _on_connect(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(engine, "connect", _on_connect)


def apply_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS audit_events_no_update
                BEFORE UPDATE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'audit_events are immutable');
                END
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
                BEFORE DELETE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'audit_events are immutable');
                END
                """
            )
        )
    _apply_additive_columns(engine)
    _record_version(engine)


def _apply_additive_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue
            present = {col["name"] for col in inspector.get_columns(table)}
            for name, ddl in columns:
                if name not in present:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def _record_version(engine: Engine) -> None:
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as db:
        row = db.get(SchemaMeta, "schema_version")
        if row is None:
            db.add(SchemaMeta(key="schema_version", value=SCHEMA_VERSION))
        else:
            row.value = SCHEMA_VERSION
        db.commit()


def schema_version(db: Session) -> str | None:
    row = db.get(SchemaMeta, "schema_version")
    return row.value if row else None
