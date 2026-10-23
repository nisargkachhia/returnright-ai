"""Synthetic demo catalog. Every merchant, policy, and purchase is hypothetical."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.clock import DEMO_AS_OF, UTC
from app.domain.models import (
    AuditEvent,
    FollowUpTask,
    MerchantPolicy,
    Order,
    OrderItem,
    PolicyRule,
    ResolutionCase,
    User,
)
from app.domain.outcomes import ELIGIBLE, HUMAN_REVIEW, INELIGIBLE, NEEDS_REVIEW, RETURN_WINDOW, WARRANTY

DISCLAIMER = (
    "HYPOTHETICAL DEMO POLICY — not an actual retailer policy. "
    "Dates, windows, and outcomes exist only for this demo."
)


def seed_demo_data(db: Session) -> None:
    settings = get_settings()
    if db.get(User, settings.demo_user_id) is not None:
        return

    as_of = DEMO_AS_OF
    db.add(
        User(
            id=settings.demo_user_id,
            display_name=settings.demo_user_display_name,
            email="alex.demo@returnright.local",
        )
    )
    db.add(User(id="other-user-9", display_name="Other Demo User", email="other@returnright.local"))

    db.add_all(
        [
            MerchantPolicy(
                id="pol-harbor-demo",
                merchant_name="DEMO Harbor Audio (synthetic)",
                title="DEMO Harbor Audio hypothetical returns v2026.1",
                version="demo-2026.1",
                effective_from=datetime(2026, 1, 1, tzinfo=UTC),
                summary="Hypothetical 30-day return window for unused audio gear. Not a real merchant policy.",
                is_hypothetical=True,
                disclaimer=DISCLAIMER,
                data_provenance="demo",
            ),
            MerchantPolicy(
                id="pol-brighthome-demo",
                merchant_name="DEMO BrightHome Appliances (synthetic)",
                title="DEMO BrightHome hypothetical warranty v2026.1",
                version="demo-2026.1",
                effective_from=datetime(2026, 1, 1, tzinfo=UTC),
                summary="Hypothetical 14-day returns and 180-day defect warranty. Not a real merchant policy.",
                is_hypothetical=True,
                disclaimer=DISCLAIMER,
                data_provenance="demo",
            ),
            MerchantPolicy(
                id="pol-review-demo",
                merchant_name="DEMO Review Lane (synthetic)",
                title="DEMO Review Lane conflicting hypothetical rules v2026.1",
                version="demo-2026.1",
                effective_from=datetime(2026, 1, 1, tzinfo=UTC),
                summary="Two hypothetical rules disagree on purpose so the engine returns NEEDS_REVIEW.",
                is_hypothetical=True,
                disclaimer=DISCLAIMER,
                data_provenance="demo",
            ),
        ]
    )

    db.add_all(
        [
            PolicyRule(
                id="rule-harbor-return-30",
                policy_id="pol-harbor-demo",
                code="DEMO-HA-RETURN-30",
                rule_kind=RETURN_WINDOW,
                issue_types="unwanted,change_of_mind",
                outcome=ELIGIBLE,
                max_days_since_purchase=30,
                requires_defect_detail=False,
                evidence_excerpt="DEMO: unused items may be returned within 30 days of the synthetic purchase date.",
                priority=10,
            ),
            PolicyRule(
                id="rule-bh-return-14",
                policy_id="pol-brighthome-demo",
                code="DEMO-BH-RETURN-14",
                rule_kind=RETURN_WINDOW,
                issue_types="unwanted,change_of_mind",
                outcome=ELIGIBLE,
                max_days_since_purchase=14,
                requires_defect_detail=False,
                evidence_excerpt="DEMO: change-of-mind returns are hypothetical for 14 days.",
                priority=10,
            ),
            PolicyRule(
                id="rule-bh-warranty-180",
                policy_id="pol-brighthome-demo",
                code="DEMO-BH-WARR-180",
                rule_kind=WARRANTY,
                issue_types="defective,malfunction",
                outcome=ELIGIBLE,
                max_days_since_purchase=180,
                requires_defect_detail=True,
                category_filter="appliances",
                evidence_excerpt="DEMO: manufacturing defects on appliances are hypothetically covered for 180 days when a defect description is present.",
                priority=20,
            ),
            PolicyRule(
                id="rule-review-allow",
                policy_id="pol-review-demo",
                code="DEMO-RV-ALLOW",
                rule_kind=RETURN_WINDOW,
                issue_types="damaged",
                outcome=ELIGIBLE,
                max_days_since_purchase=60,
                requires_defect_detail=False,
                evidence_excerpt="DEMO conflict rule A: damaged items look eligible.",
                priority=10,
            ),
            PolicyRule(
                id="rule-review-deny",
                policy_id="pol-review-demo",
                code="DEMO-RV-DENY",
                rule_kind=HUMAN_REVIEW,
                issue_types="damaged",
                outcome=INELIGIBLE,
                max_days_since_purchase=60,
                requires_defect_detail=False,
                evidence_excerpt="DEMO conflict rule B: the same damaged items look ineligible.",
                priority=10,
            ),
        ]
    )

    def order(
        order_id: str,
        user_id: str,
        merchant: str,
        number: str,
        purchased: datetime,
        total: int,
    ) -> Order:
        return Order(
            id=order_id,
            user_id=user_id,
            merchant_name=merchant,
            order_number=number,
            purchased_at=purchased,
            currency="USD",
            total_cents=total,
            data_provenance="demo",
        )

    db.add_all(
        [
            order(
                "ord-headphones",
                settings.demo_user_id,
                "DEMO Harbor Audio (synthetic)",
                "DEMO-HA-1001",
                datetime(2026, 10, 10, 15, 0, tzinfo=UTC),
                12900,
            ),
            order(
                "ord-appliance",
                settings.demo_user_id,
                "DEMO BrightHome Appliances (synthetic)",
                "DEMO-BH-4400",
                datetime(2026, 8, 1, 15, 0, tzinfo=UTC),
                8900,
            ),
            order(
                "ord-outside-window",
                settings.demo_user_id,
                "DEMO Harbor Audio (synthetic)",
                "DEMO-HA-0090",
                datetime(2026, 6, 1, 15, 0, tzinfo=UTC),
                4900,
            ),
            order(
                "ord-missing-info",
                settings.demo_user_id,
                "DEMO BrightHome Appliances (synthetic)",
                "DEMO-BH-4411",
                datetime(2026, 9, 1, 15, 0, tzinfo=UTC),
                15900,
            ),
            order(
                "ord-review",
                settings.demo_user_id,
                "DEMO Review Lane (synthetic)",
                "DEMO-RV-7",
                datetime(2026, 10, 1, 15, 0, tzinfo=UTC),
                3200,
            ),
            order(
                "ord-other-1",
                "other-user-9",
                "DEMO Harbor Audio (synthetic)",
                "DEMO-OTHER",
                datetime(2026, 10, 12, 15, 0, tzinfo=UTC),
                1999,
            ),
        ]
    )

    db.add_all(
        [
            OrderItem(
                id="item-headphones",
                order_id="ord-headphones",
                product_name="DEMO over-ear headphones (synthetic)",
                sku="DEMO-HP-1",
                quantity=1,
                unit_price_cents=12900,
                category="audio",
                condition_notes="DEMO: unused, inside the hypothetical 30-day return window relative to 2026-10-23.",
            ),
            OrderItem(
                id="item-appliance",
                order_id="ord-appliance",
                product_name="DEMO countertop blender (synthetic)",
                sku="DEMO-BL-1",
                quantity=1,
                unit_price_cents=8900,
                category="appliances",
                condition_notes="DEMO: defective appliance inside a hypothetical 180-day warranty.",
            ),
            OrderItem(
                id="item-outside",
                order_id="ord-outside-window",
                product_name="DEMO compact speaker (synthetic)",
                sku="DEMO-SP-1",
                quantity=1,
                unit_price_cents=4900,
                category="audio",
                condition_notes="DEMO: purchased outside the hypothetical 30-day return window.",
            ),
            OrderItem(
                id="item-missing-info",
                order_id="ord-missing-info",
                product_name="DEMO kettle (synthetic, incomplete report)",
                sku="DEMO-KT-1",
                quantity=1,
                unit_price_cents=15900,
                category="appliances",
                condition_notes="DEMO: serial number and defect description were not captured.",
            ),
            OrderItem(
                id="item-review",
                order_id="ord-review",
                product_name="DEMO mixed-condition gadget (synthetic)",
                sku="DEMO-MX-1",
                quantity=1,
                unit_price_cents=3200,
                category="general",
                condition_notes="DEMO: stored rules conflict and require human review.",
            ),
            OrderItem(
                id="item-other",
                order_id="ord-other-1",
                product_name="DEMO hidden other-user headphones (synthetic)",
                sku="DEMO-HID-1",
                quantity=1,
                unit_price_cents=1999,
                category="audio",
                condition_notes="DEMO: must not appear for demo-user-1.",
            ),
        ]
    )

    opened = as_of - timedelta(days=1)
    db.add(
        ResolutionCase(
            id="case-needs-review",
            user_id=settings.demo_user_id,
            order_id="ord-review",
            order_item_id="item-review",
            issue_type="damaged",
            issue_description="DEMO case: conflicting hypothetical rules require a person.",
            status="needs_review",
            eligibility_outcome=NEEDS_REVIEW,
            policy_rule_id="rule-review-allow",
            created_at=opened,
            updated_at=opened,
        )
    )
    db.add(
        AuditEvent(
            id="evt-review-created",
            case_id="case-needs-review",
            user_id=settings.demo_user_id,
            event_type="case_created",
            message="DEMO case opened for human review",
            details_json='{"demo": true, "reason": "conflicting hypothetical rules"}',
            created_at=opened,
        )
    )
    db.add(
        FollowUpTask(
            id="task-review-1",
            case_id="case-needs-review",
            title="DEMO: human review of conflicting hypothetical rules",
            due_at=as_of + timedelta(days=2),
            status="pending",
            created_at=opened,
        )
    )
    db.commit()


def reset_and_seed(db: Session) -> None:
    from app.domain.models import ResolutionAction

    for table in (
        FollowUpTask,
        AuditEvent,
        ResolutionAction,
        ResolutionCase,
        OrderItem,
        Order,
        PolicyRule,
        MerchantPolicy,
        User,
    ):
        db.query(table).delete()
    db.commit()
    seed_demo_data(db)
