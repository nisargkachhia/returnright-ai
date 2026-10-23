"""Policy catalog endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.errors import http_error
from app.db.session import get_db
from app.domain.models import MerchantPolicy
from app.repositories.policies import PolicyRepository
from app.schemas.common import Page
from app.schemas.policy import PolicyOut, PolicyRuleOut
from app.services.errors import NotFoundError

router = APIRouter(prefix="/policies", tags=["policies"])


def _policy_out(policy: MerchantPolicy) -> PolicyOut:
    return PolicyOut(
        id=policy.id,
        merchant_name=policy.merchant_name,
        title=policy.title,
        version=policy.version,
        summary=policy.summary,
        is_hypothetical=policy.is_hypothetical,
        disclaimer=policy.disclaimer,
        effective_from=policy.effective_from,
        data_provenance=policy.data_provenance,
        rules=[
            PolicyRuleOut(
                id=rule.id,
                code=rule.code,
                rule_kind=rule.rule_kind,
                issue_types=rule.issue_types,
                outcome=rule.outcome,
                max_days_since_purchase=rule.max_days_since_purchase,
                evidence_excerpt=rule.evidence_excerpt,
                data_provenance="demo",
            )
            for rule in policy.rules
        ],
    )


@router.get("", response_model=Page[PolicyOut])
def list_policies(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[PolicyOut]:
    rows, total = PolicyRepository(db).list_policies(limit=limit, offset=offset)
    return Page(items=[_policy_out(row) for row in rows], total=total, limit=limit, offset=offset)


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: str, db: Session = Depends(get_db)) -> PolicyOut:
    policy = PolicyRepository(db).get(policy_id)
    if policy is None:
        raise http_error(NotFoundError("Policy not found"))
    return _policy_out(policy)
