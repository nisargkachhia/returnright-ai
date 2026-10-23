"""Official MCP Python SDK server — Streamable HTTP tools over shared services."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from app.config import get_settings
from app.db import session as db_session
from app.schemas.cases import (
    CaseCreateRequest,
    ConfirmActionRequest,
    PrepareActionRequest,
    UpdateCaseRequest,
)
from app.schemas.policy import PolicyEvaluationRequest
from app.services.cases import CaseService
from app.services.errors import DomainError
from app.services.orders import OrderService
from app.services.policy import PolicyService

_mcp: MCPServer | None = None


def _json(data: Any) -> str:
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    return json.dumps(data, default=str)


def _error(exc: Exception) -> str:
    if isinstance(exc, DomainError):
        return _json({"error": exc.message, "code": exc.code})
    return _json({"error": str(exc), "code": "internal_error"})


def create_mcp_server() -> MCPServer:
    global _mcp
    if _mcp is not None:
        return _mcp

    settings = get_settings()
    mcp = MCPServer(
        "ReturnRight AI",
        version="0.1.0",
        instructions=(
            "ReturnRight AI helps users manage demo purchase returns and warranties. "
            "All data is synthetic. Never invent orders, policies, refunds, or real retailer submissions. "
            "Require confirm_resolution_action only after prepare_resolution_action and explicit user approval."
        ),
    )

    @mcp.tool()
    def get_demo_context(user_id: str = "") -> str:
        """Return demo mode flags and provenance notice for the current session."""
        uid = (user_id or settings.demo_user_id).strip()
        return _json(
            {
                "demo_mode": settings.demo_mode,
                "user_id": uid,
                "app": settings.app_name,
                "data_provenance": "demo",
                "notice": (
                    "Synthetic demo data only. No Alexa+ private tools or real Amazon accounts are used."
                ),
            }
        )

    @mcp.tool()
    def search_orders(query: str = "", user_id: str = "") -> str:
        """Search the current user's sample purchases by product, order ID, or merchant."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                result = OrderService(db).search(user_id=uid, query=query)
                return _json(result)
            except Exception as exc:  # noqa: BLE001 — surface as tool error payload
                return _error(exc)

    @mcp.tool()
    def get_order(order_id: str, user_id: str = "") -> str:
        """Get a single owned order with line items. Never invents missing orders."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(OrderService(db).get(user_id=uid, order_id=order_id))
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def evaluate_policy(
        order_item_id: str,
        issue_type: str,
        issue_description: str = "",
        user_id: str = "",
    ) -> str:
        """Evaluate return/warranty eligibility using stored merchant policy rules only."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                result = PolicyService(db).evaluate(
                    user_id=uid,
                    request=PolicyEvaluationRequest(
                        order_item_id=order_item_id,
                        issue_type=issue_type,
                        issue_description=issue_description,
                    ),
                )
                return _json(result)
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def create_case(
        order_id: str,
        order_item_id: str,
        issue_type: str,
        issue_description: str,
        eligibility_outcome: str = "",
        policy_rule_id: str = "",
        user_id: str = "",
    ) -> str:
        """Create a resolution case bound to an owned order item."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                result = CaseService(db).create(
                    user_id=uid,
                    request=CaseCreateRequest(
                        order_id=order_id,
                        order_item_id=order_item_id,
                        issue_type=issue_type,
                        issue_description=issue_description,
                        eligibility_outcome=eligibility_outcome or None,
                        policy_rule_id=policy_rule_id or None,
                    ),
                )
                return _json(result)
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def list_cases(user_id: str = "") -> str:
        """List resolution cases for the current user."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(CaseService(db).list(user_id=uid))
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def get_case(case_id: str, user_id: str = "") -> str:
        """Get a case with audit events, actions, and follow-ups."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(CaseService(db).get(user_id=uid, case_id=case_id))
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def update_case(case_id: str, status: str = "", note: str = "", user_id: str = "") -> str:
        """Update case status and append an audit note."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(
                    CaseService(db).update(
                        user_id=uid,
                        case_id=case_id,
                        request=UpdateCaseRequest(
                            status=status or None,
                            note=note or None,
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def list_follow_ups(case_id: str, user_id: str = "") -> str:
        """List follow-up tasks and deadlines for a case."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(CaseService(db).list_follow_ups(user_id=uid, case_id=case_id))
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def prepare_resolution_action(
        case_id: str,
        action_type: str = "return_request",
        user_id: str = "",
    ) -> str:
        """Prepare a resolution draft and confirmation token. Does not submit anything."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(
                    CaseService(db).prepare_action(
                        user_id=uid,
                        request=PrepareActionRequest(case_id=case_id, action_type=action_type),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def confirm_resolution_action(
        case_id: str,
        action_id: str,
        confirmation_token: str,
        user_confirmed: bool = False,
        user_id: str = "",
    ) -> str:
        """Commit a DEMO resolution action after explicit user confirmation. Never contacts retailers."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(
                    CaseService(db).confirm_action(
                        user_id=uid,
                        request=ConfirmActionRequest(
                            case_id=case_id,
                            action_id=action_id,
                            confirmation_token=confirmation_token,
                            user_confirmed=user_confirmed,
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    @mcp.tool()
    def simulate_failure(case_id: str, user_id: str = "") -> str:
        """Simulate a failure path without corrupting case status."""
        uid = (user_id or settings.demo_user_id).strip()
        with db_session.SessionLocal() as db:
            try:
                return _json(CaseService(db).simulate_failure(user_id=uid, case_id=case_id))
            except Exception as exc:  # noqa: BLE001
                return _error(exc)

    _mcp = mcp
    return mcp


def get_mcp_asgi_app():
    """Build the Streamable HTTP ASGI app for mounting into FastAPI."""
    settings = get_settings()
    mcp = create_mcp_server()
    return mcp.streamable_http_app(
        streamable_http_path="/",
        stateless_http=settings.mcp_stateless_http,
        json_response=settings.mcp_json_response,
    )
