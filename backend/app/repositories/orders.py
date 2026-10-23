"""Order persistence."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import Order, OrderItem


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_user(self, *, user_id: str, order_id: str) -> Order | None:
        return self.db.scalars(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.user_id == user_id)
        ).first()

    def list_for_user(self, *, user_id: str, limit: int, offset: int) -> tuple[list[Order], int]:
        base = select(Order).where(Order.user_id == user_id)
        total = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        rows = list(
            self.db.scalars(
                base.options(selectinload(Order.items))
                .order_by(Order.purchased_at.desc())
                .limit(limit)
                .offset(offset)
            ).unique().all()
        )
        return rows, total

    def search(self, *, user_id: str, query: str, limit: int, offset: int) -> tuple[list[Order], int]:
        stmt = select(Order).where(Order.user_id == user_id).options(selectinload(Order.items))
        q = query.strip()
        if q:
            pattern = f"%{q}%"
            stmt = (
                stmt.join(Order.items)
                .where(
                    or_(
                        Order.order_number.ilike(pattern),
                        Order.merchant_name.ilike(pattern),
                        Order.id.ilike(pattern),
                        OrderItem.product_name.ilike(pattern),
                        OrderItem.sku.ilike(pattern),
                    )
                )
                .distinct()
            )
        total = int(self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(
            self.db.scalars(
                stmt.order_by(Order.purchased_at.desc()).limit(limit).offset(offset)
            ).unique().all()
        )
        return rows, total

    def get_item(self, item_id: str) -> OrderItem | None:
        return self.db.get(OrderItem, item_id)
