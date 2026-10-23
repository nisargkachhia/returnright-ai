"""Order-related schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ProvenanceMixin


class OrderItemOut(BaseModel):
    id: str
    product_name: str
    sku: str
    quantity: int
    unit_price_cents: int
    category: str
    condition_notes: str


class OrderSummary(ProvenanceMixin):
    id: str
    order_number: str
    merchant_name: str
    purchased_at: datetime
    currency: str
    total_cents: int
    item_count: int


class OrderDetail(OrderSummary):
    items: list[OrderItemOut]


class SearchOrdersResponse(BaseModel):
    query: str
    results: list[OrderSummary]
    data_provenance: str = "demo"
    note: str = Field(
        default="Results are limited to synthetic demo purchases owned by the current user."
    )
