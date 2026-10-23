"""Resolution case persistence. Append-only for audit events."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import AuditEvent, FollowUpTask, ResolutionAction, ResolutionCase

ACTIVE_ACTION_STATUSES = ("awaiting_approval", "approved", "recorded")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class CaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, case: ResolutionCase) -> ResolutionCase:
        self.db.add(case)
        return case

    def get_for_user(self, *, user_id: str, case_id: str, with_relations: bool = True) -> ResolutionCase | None:
        stmt = select(ResolutionCase).where(
            ResolutionCase.id == case_id, ResolutionCase.user_id == user_id
        )
        if with_relations:
            stmt = stmt.options(
                selectinload(ResolutionCase.events),
                selectinload(ResolutionCase.follow_ups),
                selectinload(ResolutionCase.actions),
            )
        return self.db.scalars(stmt).first()

    def list_for_user(self, *, user_id: str, limit: int, offset: int) -> tuple[list[ResolutionCase], int]:
        base = select(ResolutionCase).where(ResolutionCase.user_id == user_id)
        total = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        rows = list(
            self.db.scalars(
                base.order_by(ResolutionCase.updated_at.desc()).limit(limit).offset(offset)
            ).all()
        )
        return rows, total

    def append_event(
        self,
        *,
        user_id: str,
        case_id: str | None,
        event_type: str,
        message: str,
        details: dict,
        created_at: datetime,
    ) -> AuditEvent:
        event = AuditEvent(
            id=new_id("evt"),
            case_id=case_id,
            user_id=user_id,
            event_type=event_type,
            message=message,
            details_json=json.dumps(details),
            created_at=created_at,
        )
        self.db.add(event)
        return event

    def find_active_action(self, *, case_id: str, action_type: str) -> ResolutionAction | None:
        return self.db.scalars(
            select(ResolutionAction).where(
                ResolutionAction.case_id == case_id,
                ResolutionAction.action_type == action_type,
                ResolutionAction.status.in_(ACTIVE_ACTION_STATUSES),
            )
        ).first()

    def add_action(self, action: ResolutionAction) -> ResolutionAction:
        self.db.add(action)
        return action

    def add_follow_up(self, task: FollowUpTask) -> FollowUpTask:
        self.db.add(task)
        return task

    def get_follow_up(self, *, case_id: str, task_id: str) -> FollowUpTask | None:
        return self.db.scalars(
            select(FollowUpTask).where(FollowUpTask.id == task_id, FollowUpTask.case_id == case_id)
        ).first()
