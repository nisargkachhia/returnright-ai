"""Case state machine, audit, and duplicate-action tests."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.models import AuditEvent
from app.schemas.cases import (
    ActionResultRequest,
    CaseCreateRequest,
    ConfirmActionRequest,
    DecisionRequest,
    PrepareActionRequest,
    UpdateCaseRequest,
)
from app.services.cases import CaseService
from app.services.errors import ConfirmationRequiredError, ConflictError, NotFoundError, ValidationError


def _open_case(db) -> str:
    created = CaseService(db).create(
        user_id="demo-user-1",
        request=CaseCreateRequest(
            order_id="ord-headphones",
            order_item_id="item-headphones",
            issue_type="unwanted",
            issue_description="DEMO unused headphones",
            eligibility_outcome="ELIGIBLE",
            policy_rule_id="rule-harbor-return-30",
        ),
    )
    return created.id


def test_confirmation_required(db):
    cases = CaseService(db)
    case_id = _open_case(db)
    prepared = cases.prepare_action(
        user_id="demo-user-1",
        request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
    )
    with pytest.raises(ConfirmationRequiredError):
        cases.confirm_action(
            user_id="demo-user-1",
            request=ConfirmActionRequest(
                case_id=case_id,
                action_id=prepared.action_id,
                confirmation_token=prepared.confirmation_token,
                user_confirmed=False,
            ),
        )
    detail = cases.get(user_id="demo-user-1", case_id=case_id)
    assert detail.status == "awaiting_approval"


def test_confirm_records_demo_only_and_audits(db):
    cases = CaseService(db)
    case_id = _open_case(db)
    prepared = cases.prepare_action(
        user_id="demo-user-1",
        request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
    )
    confirmed = cases.confirm_action(
        user_id="demo-user-1",
        request=ConfirmActionRequest(
            case_id=case_id,
            action_id=prepared.action_id,
            confirmation_token=prepared.confirmation_token,
            user_confirmed=True,
        ),
    )
    assert confirmed.submission_status == "demo_only"
    assert confirmed.status == "recorded"
    detail = cases.get(user_id="demo-user-1", case_id=case_id)
    assert detail.status == "action_recorded"
    event_types = [event.event_type for event in detail.events]
    assert "case_created" in event_types
    assert "action_prepared" in event_types
    assert "action_approved" in event_types
    assert "action_result_recorded" in event_types


def test_invalid_token_and_illegal_transition(db):
    cases = CaseService(db)
    case_id = _open_case(db)
    prepared = cases.prepare_action(
        user_id="demo-user-1",
        request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
    )
    with pytest.raises(ValidationError):
        cases.record_decision(
            user_id="demo-user-1",
            case_id=case_id,
            request=DecisionRequest(
                action_id=prepared.action_id,
                confirmation_token="wrong-token",
                decision="approve",
            ),
        )
    with pytest.raises(ValidationError):
        cases.update(
            user_id="demo-user-1",
            case_id=case_id,
            request=UpdateCaseRequest(status="action_recorded"),
        )


def test_prepare_is_idempotent_and_recorded_action_blocks_duplicates(db):
    cases = CaseService(db)
    case_id = _open_case(db)
    first = cases.prepare_action(
        user_id="demo-user-1",
        request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
    )
    second = cases.prepare_action(
        user_id="demo-user-1",
        request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
    )
    assert second.action_id == first.action_id
    cases.confirm_action(
        user_id="demo-user-1",
        request=ConfirmActionRequest(
            case_id=case_id,
            action_id=first.action_id,
            confirmation_token=first.confirmation_token,
            user_confirmed=True,
        ),
    )
    with pytest.raises(ConflictError):
        cases.prepare_action(
            user_id="demo-user-1",
            request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
        )
    with pytest.raises(ConflictError):
        cases.record_action_result(
            user_id="demo-user-1",
            case_id=case_id,
            action_id=first.action_id,
            request=ActionResultRequest(),
        )


def test_reject_then_resume_and_complete_follow_up(db):
    cases = CaseService(db)
    case_id = _open_case(db)
    prepared = cases.prepare_action(
        user_id="demo-user-1",
        request=PrepareActionRequest(case_id=case_id, action_type="return_request"),
    )
    rejected = cases.record_decision(
        user_id="demo-user-1",
        case_id=case_id,
        request=DecisionRequest(
            action_id=prepared.action_id,
            confirmation_token=prepared.confirmation_token,
            decision="reject",
        ),
    )
    assert rejected.status == "rejected"
    resumed = cases.update(
        user_id="demo-user-1",
        case_id=case_id,
        request=UpdateCaseRequest(status="open", note="DEMO resume"),
    )
    assert resumed.status == "open"
    task_id = resumed.follow_ups[0].id
    done = cases.complete_follow_up(user_id="demo-user-1", case_id=case_id, task_id=task_id)
    assert done.status == "completed"
    with pytest.raises(ConflictError):
        cases.complete_follow_up(user_id="demo-user-1", case_id=case_id, task_id=task_id)


def test_seeded_review_case_blocks_prepare(db):
    cases = CaseService(db)
    detail = cases.get(user_id="demo-user-1", case_id="case-needs-review")
    assert detail.status == "needs_review"
    assert detail.eligibility_outcome == "NEEDS_REVIEW"
    with pytest.raises(ValidationError):
        cases.prepare_action(
            user_id="demo-user-1",
            request=PrepareActionRequest(case_id=detail.id, action_type="return_request"),
        )


def test_unknown_case_and_other_user_are_not_found(db):
    cases = CaseService(db)
    with pytest.raises(NotFoundError):
        cases.get(user_id="demo-user-1", case_id="missing-case")
    with pytest.raises(NotFoundError):
        cases.get(user_id="other-user-9", case_id="case-needs-review")


def test_audit_events_are_immutable(db):
    event = db.query(AuditEvent).filter_by(id="evt-review-created").one()
    event.message = "tampered"
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_simulate_failure_keeps_status(db):
    cases = CaseService(db)
    case_id = _open_case(db)
    before = cases.get(user_id="demo-user-1", case_id=case_id)
    result = cases.simulate_failure(user_id="demo-user-1", case_id=case_id)
    after = cases.get(user_id="demo-user-1", case_id=case_id)
    assert result["simulated"] is True
    assert after.status == before.status
    assert any(event.event_type == "simulated_failure_recorded" for event in after.events)
    assert all(event.event_type != "simulated_failure_attempt" for event in after.events)
