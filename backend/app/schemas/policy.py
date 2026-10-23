"""Policy evaluation schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PolicyEvaluationRequest(BaseModel):
    order_item_id: str
    issue_type: str = Field(description="unwanted | change_of_mind | defective | malfunction")
    issue_description: str = Field(min_length=0, max_length=4000)


class PolicyEvidence(BaseModel):
    policy_id: str
    policy_title: str
    policy_version: str
    rule_id: str
    rule_code: str
    excerpt: str
    data_provenance: str = "demo"


class PolicyEvaluationResult(BaseModel):
    outcome: str
    reason: str
    reasons: list[str]
    evidence: list[PolicyEvidence]
    applicable_rule_code: str | None = None
    policy_version: str | None = None
    purchase_date: datetime
    evaluated_at: datetime
    window_end: datetime | None = None
    days_since_purchase: int
    requires_more_information: bool = False
    data_provenance: str = "demo"
    disclaimer: str = (
        "HYPOTHETICAL DEMO evaluation. Outcomes come only from stored demo rules, "
        "not from a real retailer and not from model judgment."
    )


class PolicyRuleOut(BaseModel):
    id: str
    code: str
    rule_kind: str
    issue_types: str
    outcome: str
    max_days_since_purchase: int | None
    evidence_excerpt: str
    data_provenance: str = "demo"


class PolicyOut(BaseModel):
    id: str
    merchant_name: str
    title: str
    version: str
    summary: str
    is_hypothetical: bool
    disclaimer: str
    effective_from: datetime
    data_provenance: str
    rules: list[PolicyRuleOut]
