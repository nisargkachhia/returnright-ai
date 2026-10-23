"""Clocks so policy and workflow tests do not depend on the wall clock."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

UTC = timezone.utc

# Fixed demo reference. Seeded windows are computed against this instant.
DEMO_AS_OF = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        self._moment = moment

    def now(self) -> datetime:
        return self._moment
