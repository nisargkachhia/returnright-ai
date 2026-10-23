"""Validated resolution-case transitions."""

from __future__ import annotations

from app.services.errors import ValidationError

OPEN = "open"
NEEDS_REVIEW = "needs_review"
AWAITING_APPROVAL = "awaiting_approval"
APPROVED = "approved"
REJECTED = "rejected"
ACTION_RECORDED = "action_recorded"
CLOSED = "closed"

CASE_TRANSITIONS: dict[str, set[str]] = {
    OPEN: {AWAITING_APPROVAL, NEEDS_REVIEW, CLOSED},
    NEEDS_REVIEW: {OPEN, CLOSED},
    AWAITING_APPROVAL: {APPROVED, REJECTED},
    APPROVED: {ACTION_RECORDED},
    REJECTED: {OPEN, CLOSED},
    ACTION_RECORDED: {CLOSED},
    CLOSED: set(),
}


def assert_transition(current: str, target: str) -> None:
    allowed = CASE_TRANSITIONS.get(current)
    if allowed is None or target not in allowed:
        raise ValidationError(f"Illegal case transition '{current}' -> '{target}'")
