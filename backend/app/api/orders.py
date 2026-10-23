"""Order REST endpoints — thin wrappers over OrderService."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user_id
from app.db.session import get_db
from app.api.errors import http_error
from app.schemas.common import Page
from app.schemas.orders import OrderDetail, OrderSummary, SearchOrdersResponse
from app.services.errors import DomainError
from app.services.orders import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=Page[OrderSummary])
def list_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> Page[OrderSummary]:
    return OrderService(db).list_orders(user_id=user_id, limit=limit, offset=offset)


@router.get("/search", response_model=SearchOrdersResponse)
def search_orders(
    q: str = Query(default=""),
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> SearchOrdersResponse:
    return OrderService(db).search(user_id=user_id, query=q)


@router.get("/{order_id}", response_model=OrderDetail)
def get_order(
    order_id: str,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> OrderDetail:
    try:
        return OrderService(db).get(user_id=user_id, order_id=order_id)
    except DomainError as exc:
        raise http_error(exc) from exc
