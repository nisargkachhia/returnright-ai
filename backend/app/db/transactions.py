"""Explicit transaction boundaries for multi-step writes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(session: Session) -> Iterator[Session]:
    """Commit on success. Roll back the whole unit of work on any error."""
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise


@contextmanager
def savepoint(session: Session) -> Iterator[Session]:
    """Nested transaction. Failure rolls back only the savepoint."""
    with session.begin_nested():
        yield session
