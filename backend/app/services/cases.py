"""Case workflow. State changes go through the state machine and one transaction."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.transactions import transaction
from app.domain.clock import UTC, Clock, FixedClock
from app.domain.models import FollowUpTask, ResolutionAction, ResolutionCase
from app.domain.outcomes import NEEDS_REVIEW
from app.domain.state_machine import (
    ACTION_RECORDED,
    APPROVED,
    AWAITING_APPROVAL,
    CLOSED,
    NEEDS_REVIEW as STATUS_NEEDS_REVIEW,
    OPEN,
    REJECTED,
    assert_transition,
)
from app.repositories.cases import CaseRepository, new_id
from app.schemas.cases import (
    ActionResultRequest,
    AuditEventOut,
    CaseCreateRequest,
    CaseDetail,
    CaseSummary,
    ConfirmActionRequest,
    DecisionRequest,
    FollowUpOut,
    PrepareActionRequest,
    PrepareActionResponse,
    ResolutionActionOut,
    UpdateCaseRequest,
)
from app.schemas.common import Page
from app.services.errors import (
    ConfirmationRequiredError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.orders import OrderService

ACTION_TYPES = {"return_request", "warranty_claim"}


class CaseService:
    def __init__(self, db: Session, clock: Clock | None = None) -> None:
        self.db = db
        self.repo = CaseRepository(db)
        self.orders = OrderService(db)
        self.settings = get_settings()
        self.clock = clock or FixedClock(self.settings.policy_as_of)

    def create(self, *, user_id: str, request: CaseCreateRequest) -> CaseDetail:
        self.orders.require_item_on_order(
            user_id=user_id,
            order_id=request.order_id,
            order_item_id=request.order_item_id,
        )
        now = self._now()
        status = STATUS_NEEDS_REVIEW if request.eligibility_outcome == NEEDS_REVIEW else OPEN
        case = ResolutionCase(
            id=new_id("case"),
            user_id=user_id,
            order_id=request.order_id,
            order_item_id=request.order_item_id,
            issue_type=request.issue_type.strip().lower(),
            issue_description=request.issue_description.strip(),
            status=status,
            eligibility_outcome=request.eligibility_outcome,
            policy_rule_id=request.policy_rule_id,
            created_at=now,
            updated_at=now,
        )
        with transaction(self.db):
            self.repo.add(case)
            self.repo.append_event(
                user_id=user_id,
                case_id=case.id,
                event_type="case_created",
                message="Resolution case opened",
                details={"issue_type": case.issue_type, "status": status},
                created_at=now,
            )
            self.repo.add_follow_up(
                FollowUpTask(
                    id=new_id("task"),
                    case_id=case.id,
                    title="Review prepared resolution draft",
                    due_at=now + timedelta(days=3),
                    status="pending",
                    created_at=now,
                )
            )
        return self.get(user_id=user_id, case_id=case.id)

    def list(self, *, user_id: str) -> list[CaseSummary]:
        page = self.list_page(user_id=user_id, limit=100, offset=0)
        return page.items

    def list_page(self, *, user_id: str, limit: int, offset: int) -> Page[CaseSummary]:
        rows, total = self.repo.list_for_user(user_id=user_id, limit=limit, offset=offset)
        return Page(items=[_summary(row) for row in rows], total=total, limit=limit, offset=offset)

    def get(self, *, user_id: str, case_id: str) -> CaseDetail:
        return _detail(self._owned(user_id=user_id, case_id=case_id))

    def list_events(self, *, user_id: str, case_id: str) -> list[AuditEventOut]:
        case = self._owned(user_id=user_id, case_id=case_id)
        return [
            AuditEventOut(id=event.id, event_type=event.event_type, message=event.message, created_at=event.created_at)
            for event in sorted(case.events, key=lambda row: row.created_at)
        ]

    def update(self, *, user_id: str, case_id: str, request: UpdateCaseRequest) -> CaseDetail:
        case = self._owned(user_id=user_id, case_id=case_id)
        now = self._now()
        with transaction(self.db):
            if request.status:
                target = request.status.strip().lower()
                assert_transition(case.status, target)
                case.status = target
            case.updated_at = now
            self.repo.append_event(
                user_id=user_id,
                case_id=case.id,
                event_type="case_updated",
                message="Case updated",
                details={"status": case.status, "note": request.note},
                created_at=now,
            )
        return self.get(user_id=user_id, case_id=case.id)

    def prepare_action(self, *, user_id: str, request: PrepareActionRequest) -> PrepareActionResponse:
        case = self._owned(user_id=user_id, case_id=request.case_id)
        action_type = request.action_type.strip().lower()
        if action_type not in ACTION_TYPES:
            raise ValidationError("action_type must be return_request or warranty_claim")

        existing = self.repo.find_active_action(case_id=case.id, action_type=action_type)
        if existing is not None:
            if existing.status == AWAITING_APPROVAL:
                return _prepared(existing, case, self.settings.confirmation_token_ttl_seconds)
            raise ConflictError("A consequential action of this type already exists for the case")

        if case.status == STATUS_NEEDS_REVIEW or case.eligibility_outcome == NEEDS_REVIEW:
            raise ValidationError("Case requires human review before an action can be prepared")
        if case.status != OPEN:
            raise ValidationError(
                f"Actions can only be prepared from '{OPEN}', current status is '{case.status}'"
            )

        now = self._now()
        token = secrets.token_urlsafe(24)
        action = ResolutionAction(
            id=new_id("act"),
            case_id=case.id,
            action_type=action_type,
            status=AWAITING_APPROVAL,
            payload_json=json.dumps(
                {
                    "order_id": case.order_id,
                    "order_item_id": case.order_item_id,
                    "issue_type": case.issue_type,
                    "eligibility_outcome": case.eligibility_outcome,
                    "demo": True,
                }
            ),
            confirmation_token=token,
            submission_status="demo_only",
            created_at=now,
        )
        with transaction(self.db):
            assert_transition(case.status, AWAITING_APPROVAL)
            self.repo.add_action(action)
            case.status = AWAITING_APPROVAL
            case.updated_at = now
            self.repo.append_event(
                user_id=user_id,
                case_id=case.id,
                event_type="action_prepared",
                message=f"Prepared {action_type} draft awaiting approval",
                details={"action_id": action.id},
                created_at=now,
            )
        return _prepared(action, case, self.settings.confirmation_token_ttl_seconds)

    def record_decision(self, *, user_id: str, case_id: str, request: DecisionRequest) -> CaseDetail:
        decision = request.decision.strip().lower()
        if decision not in {"approve", "reject"}:
            raise ValidationError("decision must be approve or reject")
        case = self._owned(user_id=user_id, case_id=case_id)
        action = _find_action(case, request.action_id)
        self._require_token(action, request.confirmation_token)
        now = self._now()
        target = APPROVED if decision == "approve" else REJECTED
        with transaction(self.db):
            assert_transition(case.status, target)
            action.status = target
            action.decided_at = now
            action.confirmation_token = None
            case.status = target
            case.updated_at = now
            self.repo.append_event(
                user_id=user_id,
                case_id=case.id,
                event_type="action_approved" if decision == "approve" else "action_rejected",
                message=f"User {decision}d the demo resolution action",
                details={"action_id": action.id},
                created_at=now,
            )
        return self.get(user_id=user_id, case_id=case.id)

    def record_action_result(
        self, *, user_id: str, case_id: str, action_id: str, request: ActionResultRequest
    ) -> ResolutionActionOut:
        case = self._owned(user_id=user_id, case_id=case_id)
        action = _find_action(case, action_id)
        if action.status == "recorded":
            raise ConflictError("Action result was already recorded")
        now = self._now()
        with transaction(self.db):
            assert_transition(case.status, ACTION_RECORDED)
            if action.status != APPROVED:
                raise ConflictError("Action must be approved before a result is recorded")
            action.status = "recorded"
            action.result_note = request.result_note
            action.result_recorded_at = now
            action.submission_status = "demo_only"
            case.status = ACTION_RECORDED
            case.updated_at = now
            self.repo.append_event(
                user_id=user_id,
                case_id=case.id,
                event_type="action_result_recorded",
                message="Demo action result recorded. No real retailer request was submitted.",
                details={"action_id": action.id, "submission_status": "demo_only"},
                created_at=now,
            )
            self.repo.add_follow_up(
                FollowUpTask(
                    id=new_id("task"),
                    case_id=case.id,
                    title="Track demo resolution follow-up",
                    due_at=now + timedelta(days=7),
                    status="pending",
                    created_at=now,
                )
            )
        self.db.refresh(action)
        return _action_out(action)

    def confirm_action(self, *, user_id: str, request: ConfirmActionRequest) -> ResolutionActionOut:
        if not request.user_confirmed:
            raise ConfirmationRequiredError("user_confirmed must be true")
        self.record_decision(
            user_id=user_id,
            case_id=request.case_id,
            request=DecisionRequest(
                action_id=request.action_id,
                confirmation_token=request.confirmation_token,
                decision="approve",
            ),
        )
        return self.record_action_result(
            user_id=user_id,
            case_id=request.case_id,
            action_id=request.action_id,
            request=ActionResultRequest(),
        )

    def list_follow_ups(self, *, user_id: str, case_id: str) -> list[FollowUpOut]:
        case = self._owned(user_id=user_id, case_id=case_id)
        return [_follow_up(task) for task in case.follow_ups]

    def complete_follow_up(self, *, user_id: str, case_id: str, task_id: str) -> FollowUpOut:
        case = self._owned(user_id=user_id, case_id=case_id)
        task = self.repo.get_follow_up(case_id=case.id, task_id=task_id)
        if task is None:
            raise NotFoundError("Follow-up task not found")
        if task.status == "completed":
            raise ConflictError("Follow-up task is already completed")
        now = self._now()
        with transaction(self.db):
            task.status = "completed"
            task.completed_at = now
            self.repo.append_event(
                user_id=user_id,
                case_id=case.id,
                event_type="follow_up_completed",
                message=f"Completed follow-up '{task.title}'",
                details={"task_id": task.id},
                created_at=now,
            )
        return _follow_up(task)

    def close(self, *, user_id: str, case_id: str) -> CaseDetail:
        return self.update(
            user_id=user_id,
            case_id=case_id,
            request=UpdateCaseRequest(status=CLOSED, note="closed"),
        )

    def simulate_failure(self, *, user_id: str, case_id: str) -> dict:
        case = self._owned(user_id=user_id, case_id=case_id, with_relations=False)
        before_status = case.status
        try:
            with self.db.begin_nested():
                self.repo.append_event(
                    user_id=user_id,
                    case_id=case.id,
                    event_type="simulated_failure_attempt",
                    message="Simulated failure; this attempt is rolled back",
                    details={},
                    created_at=self._now(),
                )
                raise RuntimeError("Simulated failure for demo/testing")
        except RuntimeError as exc:
            self.db.rollback()
            case = self._owned(user_id=user_id, case_id=case_id, with_relations=False)
            if case.status != before_status:
                raise ConflictError("Simulated failure changed case status") from exc
            with transaction(self.db):
                self.repo.append_event(
                    user_id=user_id,
                    case_id=case.id,
                    event_type="simulated_failure_recorded",
                    message=str(exc),
                    details={"case_status_unchanged": case.status},
                    created_at=self._now(),
                )
            return {
                "ok": False,
                "simulated": True,
                "case_id": case.id,
                "case_status": case.status,
                "message": "Failure simulated; case status unchanged",
                "data_provenance": "demo",
            }

    def _owned(self, *, user_id: str, case_id: str, with_relations: bool = True) -> ResolutionCase:
        case = self.repo.get_for_user(user_id=user_id, case_id=case_id, with_relations=with_relations)
        if case is None:
            raise NotFoundError("Case not found for this user")
        return case

    def _now(self) -> datetime:
        moment = self.clock.now()
        if moment.tzinfo is None:
            return moment.replace(tzinfo=UTC)
        return moment

    def _require_token(self, action: ResolutionAction, token: str) -> None:
        if action.status != AWAITING_APPROVAL:
            raise ConflictError("Action is not awaiting approval")
        if action.confirmation_token != token:
            raise ValidationError("Invalid confirmation token")
        created = action.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if self._now() - created > timedelta(seconds=self.settings.confirmation_token_ttl_seconds):
            raise ValidationError("Confirmation token expired")


def _find_action(case: ResolutionCase, action_id: str) -> ResolutionAction:
    action = next((row for row in case.actions if row.id == action_id), None)
    if action is None:
        raise NotFoundError("Action not found for case")
    return action


def _prepared(action: ResolutionAction, case: ResolutionCase, ttl: int) -> PrepareActionResponse:
    if not action.confirmation_token:
        raise ConflictError("Prepared action is missing a confirmation token")
    return PrepareActionResponse(
        draft_summary=(
            f"DEMO draft {action.action_type} for case {case.id} "
            f"(item {case.order_item_id}, outcome={case.eligibility_outcome or 'n/a'})."
        ),
        action_id=action.id,
        confirmation_token=action.confirmation_token,
        expires_in_seconds=ttl,
    )


def _summary(case: ResolutionCase) -> CaseSummary:
    return CaseSummary(
        id=case.id,
        order_id=case.order_id,
        order_item_id=case.order_item_id,
        issue_type=case.issue_type,
        status=case.status,
        eligibility_outcome=case.eligibility_outcome,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def _detail(case: ResolutionCase) -> CaseDetail:
    events = sorted(case.events, key=lambda event: event.created_at)
    return CaseDetail(
        **_summary(case).model_dump(),
        issue_description=case.issue_description,
        policy_rule_id=case.policy_rule_id,
        events=[
            AuditEventOut(
                id=event.id,
                event_type=event.event_type,
                message=event.message,
                created_at=event.created_at,
            )
            for event in events
        ],
        follow_ups=[_follow_up(task) for task in case.follow_ups],
        actions=[_action_out(action) for action in case.actions],
    )


def _follow_up(task: FollowUpTask) -> FollowUpOut:
    return FollowUpOut(id=task.id, title=task.title, due_at=task.due_at, status=task.status)


def _action_out(action: ResolutionAction) -> ResolutionActionOut:
    return ResolutionActionOut(
        id=action.id,
        action_type=action.action_type,
        status=action.status,
        submission_status=action.submission_status,
        confirmed_at=action.confirmed_at or action.result_recorded_at,
        created_at=action.created_at,
    )
