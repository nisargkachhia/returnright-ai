"""Order search and retrieval. Persistence lives in OrderRepository."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.models import Order, OrderItem
from app.repositories.orders import OrderRepository
from app.schemas.common import Page
from app.schemas.orders import OrderDetail, OrderItemOut, OrderSummary, SearchOrdersResponse
from app.services.errors import NotFoundError, ValidationError


def to_summary(order: Order) -> OrderSummary:
    return OrderSummary(
        id=order.id,
        order_number=order.order_number,
        merchant_name=order.merchant_name,
        purchased_at=order.purchased_at,
        currency=order.currency,
        total_cents=order.total_cents,
        item_count=len(order.items),
        data_provenance=order.data_provenance,
    )


def to_detail(order: Order) -> OrderDetail:
    return OrderDetail(
        **to_summary(order).model_dump(),
        items=[
            OrderItemOut(
                id=item.id,
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price_cents=item.unit_price_cents,
                category=item.category,
                condition_notes=item.condition_notes,
            )
            for item in order.items
        ],
    )


class OrderService:
    def __init__(self, db: Session) -> None:
        self.repo = OrderRepository(db)

    def search(
        self, *, user_id: str, query: str, limit: int = 20, offset: int = 0
    ) -> SearchOrdersResponse:
        rows, _total = self.repo.search(user_id=user_id, query=query, limit=limit, offset=offset)
        return SearchOrdersResponse(query=query.strip(), results=[to_summary(row) for row in rows])

    def list_orders(self, *, user_id: str, limit: int, offset: int) -> Page[OrderSummary]:
        rows, total = self.repo.list_for_user(user_id=user_id, limit=limit, offset=offset)
        return Page(items=[to_summary(row) for row in rows], total=total, limit=limit, offset=offset)

    def get(self, *, user_id: str, order_id: str) -> OrderDetail:
        order = self.repo.get_for_user(user_id=user_id, order_id=order_id)
        if order is None:
            raise NotFoundError("Order not found for this user")
        return to_detail(order)

    def get_owned_item(self, *, user_id: str, order_item_id: str) -> tuple[Order, OrderItem]:
        item = self.repo.get_item(order_item_id)
        if item is None:
            raise NotFoundError("Order item not found")
        order = self.repo.get_for_user(user_id=user_id, order_id=item.order_id)
        if order is None:
            raise NotFoundError("Order item not found for this user")
        owned = next((row for row in order.items if row.id == item.id), item)
        return order, owned

    def require_item_on_order(
        self, *, user_id: str, order_id: str, order_item_id: str
    ) -> tuple[Order, OrderItem]:
        order, item = self.get_owned_item(user_id=user_id, order_item_id=order_item_id)
        if order.id != order_id:
            raise ValidationError("order_item_id does not belong to order_id")
        return order, item
