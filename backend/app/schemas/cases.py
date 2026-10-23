"""Resolution case schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    order_id: str
    order_item_id: str
    issue_type: str
    issue_description: str = Field(min_length=1, max_length=4000)
    eligibility_outcome: str | None = None
    policy_rule_id: str | None = None


class UpdateCaseRequest(BaseModel):
    status: str | None = None
    note: str | None = Field(default=None, max_length=2000)


class AuditEventOut(BaseModel):
    id: str
    event_type: str
    message: str
    created_at: datetime


class FollowUpOut(BaseModel):
    id: str
    title: str
    due_at: datetime
    status: str


class ResolutionActionOut(BaseModel):
    id: str
    action_type: str
    status: str
    submission_status: str
    confirmed_at: datetime | None
    created_at: datetime


class CaseSummary(BaseModel):
    id: str
    order_id: str
    order_item_id: str
    issue_type: str
    status: str
    eligibility_outcome: str | None
    created_at: datetime
    updated_at: datetime


class CaseDetail(CaseSummary):
    issue_description: str
    policy_rule_id: str | None
    events: list[AuditEventOut]
    follow_ups: list[FollowUpOut]
    actions: list[ResolutionActionOut]
    data_provenance: str = "demo"


class PrepareActionRequest(BaseModel):
    case_id: str
    action_type: str = Field(description="return_request | warranty_claim")


class PrepareActionResponse(BaseModel):
    draft_summary: str
    action_id: str
    confirmation_token: str
    expires_in_seconds: int
    requires_explicit_confirmation: bool = True
    submission_status_if_confirmed: str = "demo_only"
    warning: str = (
        "Confirming will record a DEMO resolution action only. "
        "No real retailer request will be submitted."
    )


class ConfirmActionRequest(BaseModel):
    case_id: str
    action_id: str
    confirmation_token: str
    user_confirmed: bool = Field(
        description="Must be true. Explicit approval is required.",
    )


class DecisionRequest(BaseModel):
    action_id: str
    confirmation_token: str
    decision: str = Field(description="approve | reject")


class ActionResultRequest(BaseModel):
    result_note: str = Field(
        default="DEMO result recorded. No retailer request was submitted.",
        max_length=2000,
    )


class FollowUpCompleteResponse(BaseModel):
    id: str
    title: str
    status: str
    completed_at: datetime | None
