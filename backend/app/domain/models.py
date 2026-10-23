"""SQLAlchemy models for ReturnRight domain entities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list[Order]] = relationship(back_populates="user")
    cases: Mapped[list[ResolutionCase]] = relationship(back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    merchant_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    data_provenance: Mapped[str] = mapped_column(String(32), default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "order_number", name="uq_user_order_number"),)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general")
    condition_notes: Mapped[str] = mapped_column(Text, default="")

    order: Mapped[Order] = relationship(back_populates="items")


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    is_hypothetical: Mapped[bool] = mapped_column(Boolean, default=True)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="HYPOTHETICAL DEMO POLICY — not an actual retailer policy.",
    )
    data_provenance: Mapped[str] = mapped_column(String(32), default="demo")

    rules: Mapped[list[PolicyRule]] = relationship(back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("merchant_policies.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_kind: Mapped[str] = mapped_column(String(32), default="return_window")
    issue_types: Mapped[str] = mapped_column(String(255), nullable=False)  # comma-separated
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    max_days_since_purchase: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requires_defect_detail: Mapped[bool] = mapped_column(Boolean, default=False)
    category_filter: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)

    policy: Mapped[MerchantPolicy] = relationship(back_populates="rules")

    __table_args__ = (Index("ix_policy_rules_policy_code", "policy_id", "code"),)


class ResolutionCase(Base):
    __tablename__ = "resolution_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id: Mapped[str] = mapped_column(ForeignKey("order_items.id"), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="open", index=True)
    eligibility_outcome: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    policy_rule_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="cases")
    actions: Mapped[list[ResolutionAction]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    events: Mapped[list[AuditEvent]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[list[FollowUpTask]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class ResolutionAction(Base):
    __tablename__ = "resolution_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("resolution_cases.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    confirmation_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    result_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_status: Mapped[str] = mapped_column(String(64), default="demo_only")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped[ResolutionCase] = relationship(back_populates="actions")

    __table_args__ = (
        Index(
            "uq_active_resolution_action",
            "case_id",
            "action_type",
            unique=True,
            sqlite_where=text("status IN ('awaiting_approval', 'approved', 'recorded')"),
        ),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[Optional[str]] = mapped_column(ForeignKey("resolution_cases.id"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped[Optional[ResolutionCase]] = relationship(back_populates="events")


class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("resolution_cases.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped[ResolutionCase] = relationship(back_populates="follow_ups")


class SchemaMeta(Base):
    __tablename__ = "schema_meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
