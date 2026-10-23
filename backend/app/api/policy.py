"""Policy evaluation REST endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user_id
from app.api.errors import http_error
from app.db.session import get_db
from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResult
from app.services.errors import DomainError
from app.services.policy import PolicyService

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/evaluate", response_model=PolicyEvaluationResult)
def evaluate_policy(
    body: PolicyEvaluationRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> PolicyEvaluationResult:
    try:
        return PolicyService(db).evaluate(user_id=user_id, request=body)
    except DomainError as exc:
        raise http_error(exc) from exc
