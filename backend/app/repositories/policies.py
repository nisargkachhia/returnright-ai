"""Merchant policy persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import MerchantPolicy


class PolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_policies(self, *, limit: int, offset: int) -> tuple[list[MerchantPolicy], int]:
        from sqlalchemy import func

        total = int(self.db.scalar(select(func.count()).select_from(MerchantPolicy)) or 0)
        rows = list(
            self.db.scalars(
                select(MerchantPolicy)
                .options(selectinload(MerchantPolicy.rules))
                .order_by(MerchantPolicy.merchant_name, MerchantPolicy.effective_from)
                .limit(limit)
                .offset(offset)
            ).unique().all()
        )
        return rows, total

    def get(self, policy_id: str) -> MerchantPolicy | None:
        return self.db.scalars(
            select(MerchantPolicy)
            .options(selectinload(MerchantPolicy.rules))
            .where(MerchantPolicy.id == policy_id)
        ).first()

    def active_for_merchant(self, *, merchant_name: str, on_date: datetime) -> MerchantPolicy | None:
        rows = list(
            self.db.scalars(
                select(MerchantPolicy)
                .options(selectinload(MerchantPolicy.rules))
                .where(MerchantPolicy.merchant_name == merchant_name)
                .order_by(MerchantPolicy.effective_from.desc())
            ).unique().all()
        )
        chosen: MerchantPolicy | None = None
        for policy in rows:
            start = policy.effective_from
            if start.tzinfo is None:
                start = start.replace(tzinfo=on_date.tzinfo)
            if start > on_date:
                continue
            end = policy.effective_to
            if end is not None:
                if end.tzinfo is None:
                    end = end.replace(tzinfo=on_date.tzinfo)
                if end < on_date:
                    continue
            chosen = policy
            break
        return chosen
