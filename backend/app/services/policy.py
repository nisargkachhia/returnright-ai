"""Deterministic policy engine. Stored rules decide the outcome; text cannot override it."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.clock import Clock, FixedClock
from app.domain.models import MerchantPolicy, PolicyRule
from app.domain.outcomes import (
    ELIGIBLE,
    HUMAN_REVIEW,
    INELIGIBLE,
    NEEDS_INFORMATION,
    NEEDS_REVIEW,
)
from app.repositories.policies import PolicyRepository
from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResult, PolicyEvidence
from app.services.errors import ValidationError
from app.services.orders import OrderService

ALLOWED_ISSUE_TYPES = {"unwanted", "change_of_mind", "defective", "malfunction", "damaged"}
MIN_DEFECT_DETAIL = 12


class PolicyService:
    def __init__(self, db: Session, clock: Clock | None = None) -> None:
        self.db = db
        self.orders = OrderService(db)
        self.policies = PolicyRepository(db)
        self.clock = clock or FixedClock(get_settings().policy_as_of)

    def evaluate(self, *, user_id: str, request: PolicyEvaluationRequest) -> PolicyEvaluationResult:
        issue_type = request.issue_type.strip().lower()
        if issue_type not in ALLOWED_ISSUE_TYPES:
            raise ValidationError(
                f"Unsupported issue_type. Allowed: {', '.join(sorted(ALLOWED_ISSUE_TYPES))}"
            )

        # Description is untrusted data. It never selects or overrides an outcome.
        description = (request.issue_description or "").strip()
        order, item = self.orders.get_owned_item(user_id=user_id, order_item_id=request.order_item_id)
        evaluated_at = _aware(self.clock.now())
        purchased = _aware(order.purchased_at)
        days = max(0, (evaluated_at - purchased).days)

        policy = self.policies.active_for_merchant(merchant_name=order.merchant_name, on_date=purchased)
        if policy is None:
            return _result(
                outcome=NEEDS_INFORMATION,
                reason=f"No stored demo policy covers '{order.merchant_name}' on the purchase date.",
                reasons=[
                    f"No stored demo policy covers '{order.merchant_name}' on the purchase date.",
                    "Policy terms are not invented.",
                ],
                evidence=[],
                days=days,
                purchased=purchased,
                evaluated_at=evaluated_at,
                window_end=None,
                policy_version=None,
                rule_code=None,
            )

        matching = [
            rule
            for rule in sorted(policy.rules, key=lambda row: (row.priority, row.code))
            if issue_type in {part.strip() for part in rule.issue_types.split(",")}
            and (not rule.category_filter or rule.category_filter == item.category)
        ]
        if not matching:
            return _result(
                outcome=NEEDS_INFORMATION,
                reason=f"No documented demo rule covers issue_type '{issue_type}'.",
                reasons=[
                    f"No documented demo rule covers issue_type '{issue_type}'.",
                    "Eligibility is not inferred beyond stored rules.",
                ],
                evidence=[],
                days=days,
                purchased=purchased,
                evaluated_at=evaluated_at,
                window_end=None,
                policy_version=policy.version,
                rule_code=None,
            )

        applicable: list[tuple[PolicyRule, str]] = []
        needs_detail: list[PolicyRule] = []
        expired: list[PolicyRule] = []

        for rule in matching:
            if rule.rule_kind == HUMAN_REVIEW or rule.outcome == NEEDS_REVIEW:
                applicable.append((rule, NEEDS_REVIEW))
                continue
            if rule.max_days_since_purchase is not None and days > rule.max_days_since_purchase:
                expired.append(rule)
                continue
            if rule.requires_defect_detail and len(description) < MIN_DEFECT_DETAIL:
                needs_detail.append(rule)
                continue
            applicable.append((rule, rule.outcome))

        if not applicable and needs_detail:
            rule = needs_detail[0]
            return _result(
                outcome=NEEDS_INFORMATION,
                reason="A documented demo rule needs a clearer defect description before it can apply.",
                reasons=[
                    "A documented demo rule needs a clearer defect description before it can apply.",
                    f"Rule {rule.code} was not applied because the description is too short.",
                ],
                evidence=[_evidence(policy, rule)],
                days=days,
                purchased=purchased,
                evaluated_at=evaluated_at,
                window_end=_window_end(purchased, rule),
                policy_version=policy.version,
                rule_code=rule.code,
            )

        if not applicable and expired:
            rule = min(expired, key=lambda row: row.priority)
            end = _window_end(purchased, rule)
            return _result(
                outcome=INELIGIBLE,
                reason=(
                    f"Purchase is outside the documented demo window for rule {rule.code} "
                    f"({days} days; window ends {end.date() if end else 'n/a'})."
                ),
                reasons=[
                    f"Purchase is outside the documented demo window for rule {rule.code}.",
                    f"Purchase age is {days} day(s).",
                ],
                evidence=[_evidence(policy, rule)],
                days=days,
                purchased=purchased,
                evaluated_at=evaluated_at,
                window_end=end,
                policy_version=policy.version,
                rule_code=rule.code,
            )

        outcomes = {outcome for _, outcome in applicable}
        if len(outcomes) > 1 or NEEDS_REVIEW in outcomes and len(applicable) > 1 and len(outcomes) > 1:
            return _conflict(policy, applicable, days, purchased, evaluated_at)

        if NEEDS_REVIEW in outcomes:
            rule = next(rule for rule, outcome in applicable if outcome == NEEDS_REVIEW)
            return _result(
                outcome=NEEDS_REVIEW,
                reason=f"Documented demo rule {rule.code} requires human review.",
                reasons=[f"Documented demo rule {rule.code} requires human review."],
                evidence=[_evidence(policy, rule)],
                days=days,
                purchased=purchased,
                evaluated_at=evaluated_at,
                window_end=_window_end(purchased, rule),
                policy_version=policy.version,
                rule_code=rule.code,
            )

        if len(outcomes) > 1:
            return _conflict(policy, applicable, days, purchased, evaluated_at)

        rule, outcome = applicable[0]
        if outcome not in {ELIGIBLE, INELIGIBLE, NEEDS_INFORMATION, NEEDS_REVIEW}:
            outcome = NEEDS_REVIEW
        return _result(
            outcome=outcome,
            reason=f"Documented demo rule {rule.code} ({rule.rule_kind}) applies.",
            reasons=[
                f"Documented demo rule {rule.code} ({rule.rule_kind}) applies.",
                f"Purchase age is {days} day(s).",
            ],
            evidence=[_evidence(policy, rule)],
            days=days,
            purchased=purchased,
            evaluated_at=evaluated_at,
            window_end=_window_end(purchased, rule),
            policy_version=policy.version,
            rule_code=rule.code,
        )


def _conflict(
    policy: MerchantPolicy,
    applicable: list[tuple[PolicyRule, str]],
    days: int,
    purchased: datetime,
    evaluated_at: datetime,
) -> PolicyEvaluationResult:
    codes = ", ".join(rule.code for rule, _outcome in applicable)
    return _result(
        outcome=NEEDS_REVIEW,
        reason=f"Stored demo rules conflict ({codes}) and require human review.",
        reasons=[
            f"Stored demo rules conflict ({codes}).",
            "The engine does not pick a winner when documented outcomes disagree.",
        ],
        evidence=[_evidence(policy, rule) for rule, _outcome in applicable],
        days=days,
        purchased=purchased,
        evaluated_at=evaluated_at,
        window_end=None,
        policy_version=policy.version,
        rule_code=None,
    )


def _window_end(purchased: datetime, rule: PolicyRule) -> datetime | None:
    if rule.max_days_since_purchase is None:
        return None
    return purchased + timedelta(days=rule.max_days_since_purchase)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _evidence(policy: MerchantPolicy, rule: PolicyRule) -> PolicyEvidence:
    return PolicyEvidence(
        policy_id=policy.id,
        policy_title=policy.title,
        policy_version=policy.version,
        rule_id=rule.id,
        rule_code=rule.code,
        excerpt=rule.evidence_excerpt,
        data_provenance=policy.data_provenance,
    )


def _result(
    *,
    outcome: str,
    reason: str,
    reasons: list[str],
    evidence: list[PolicyEvidence],
    days: int,
    purchased: datetime,
    evaluated_at: datetime,
    window_end: datetime | None,
    policy_version: str | None,
    rule_code: str | None,
) -> PolicyEvaluationResult:
    return PolicyEvaluationResult(
        outcome=outcome,
        reason=reason,
        reasons=reasons,
        evidence=evidence,
        days_since_purchase=days,
        requires_more_information=outcome == NEEDS_INFORMATION,
        purchase_date=purchased,
        evaluated_at=evaluated_at,
        window_end=window_end,
        policy_version=policy_version,
        applicable_rule_code=rule_code,
        data_provenance="demo",
    )
