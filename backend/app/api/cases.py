"""Case REST endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user_id
from app.api.errors import http_error
from app.db.session import get_db
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
from app.services.cases import CaseService
from app.services.errors import DomainError

router = APIRouter(prefix="/cases", tags=["cases"])


def _http(exc: DomainError) -> HTTPException:
    return http_error(exc)


@router.get("", response_model=Page[CaseSummary])
def list_cases(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> Page[CaseSummary]:
    return CaseService(db).list_page(user_id=user_id, limit=limit, offset=offset)


@router.post("", response_model=CaseDetail)
def create_case(
    body: CaseCreateRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> CaseDetail:
    try:
        return CaseService(db).create(user_id=user_id, request=body)
    except DomainError as exc:
        raise _http(exc) from exc


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: str,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> CaseDetail:
    try:
        return CaseService(db).get(user_id=user_id, case_id=case_id)
    except DomainError as exc:
        raise _http(exc) from exc


@router.patch("/{case_id}", response_model=CaseDetail)
def update_case(
    case_id: str,
    body: UpdateCaseRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> CaseDetail:
    try:
        return CaseService(db).update(user_id=user_id, case_id=case_id, request=body)
    except DomainError as exc:
        raise _http(exc) from exc


@router.get("/{case_id}/follow-ups", response_model=list[FollowUpOut])
def list_follow_ups(
    case_id: str,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> list[FollowUpOut]:
    try:
        return CaseService(db).list_follow_ups(user_id=user_id, case_id=case_id)
    except DomainError as exc:
        raise _http(exc) from exc


@router.post("/actions/prepare", response_model=PrepareActionResponse)
def prepare_action(
    body: PrepareActionRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> PrepareActionResponse:
    try:
        return CaseService(db).prepare_action(user_id=user_id, request=body)
    except DomainError as exc:
        raise _http(exc) from exc


@router.post("/actions/confirm", response_model=ResolutionActionOut)
def confirm_action(
    body: ConfirmActionRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> ResolutionActionOut:
    try:
        return CaseService(db).confirm_action(user_id=user_id, request=body)
    except DomainError as exc:
        raise _http(exc) from exc


@router.get("/{case_id}/events", response_model=list[AuditEventOut])
def list_events(
    case_id: str,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> list[AuditEventOut]:
    try:
        return CaseService(db).list_events(user_id=user_id, case_id=case_id)
    except DomainError as exc:
        raise _http(exc) from exc


@router.post("/{case_id}/follow-ups/{task_id}/complete", response_model=FollowUpOut)
def complete_follow_up(
    case_id: str,
    task_id: str,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> FollowUpOut:
    try:
        return CaseService(db).complete_follow_up(user_id=user_id, case_id=case_id, task_id=task_id)
    except DomainError as exc:
        raise _http(exc) from exc


@router.post("/{case_id}/decisions", response_model=CaseDetail)
def record_decision(
    case_id: str,
    body: DecisionRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> CaseDetail:
    try:
        return CaseService(db).record_decision(user_id=user_id, case_id=case_id, request=body)
    except DomainError as exc:
        raise _http(exc) from exc


@router.post("/{case_id}/actions/{action_id}/result", response_model=ResolutionActionOut)
def record_action_result(
    case_id: str,
    action_id: str,
    body: ActionResultRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> ResolutionActionOut:
    try:
        return CaseService(db).record_action_result(
            user_id=user_id, case_id=case_id, action_id=action_id, request=body
        )
    except DomainError as exc:
        raise _http(exc) from exc


@router.post("/{case_id}/simulate-failure")
def simulate_failure(
    case_id: str,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return CaseService(db).simulate_failure(user_id=user_id, case_id=case_id)
    except DomainError as exc:
        raise _http(exc) from exc
