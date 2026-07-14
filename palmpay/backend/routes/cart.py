"""Cart APIs — guest (X-Session-Id) + authenticated merge."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db
from backend.deps_auth import get_current_account, get_optional_account
from backend.shop import cart_service as svc

router = APIRouter(prefix="/api/cart", tags=["cart"])


class CartItemOut(BaseModel):
    id: int
    product_id: int
    product_slug: str
    name: str
    image_url: Optional[str] = None
    quantity: int
    unit_price: float
    price_at_add: float
    line_total: float
    stock_qty: int
    shop_id: int
    shop_name: Optional[str] = None


class CartResponse(BaseModel):
    cart_id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    item_count: int
    items: list[CartItemOut]
    subtotal_pkr: float
    platform_fee_pkr: float
    total_pkr: float
    warnings: list[str] = Field(default_factory=list)
    updated_at: datetime


class AddItemBody(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=999)


class UpdateItemBody(BaseModel):
    quantity: int = Field(..., ge=1, le=999)


class MergeBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=255)


def _resolve_cart(
    db: Session,
    account: models.Account | None,
    session_id: str | None,
) -> models.Cart:
    return svc.get_or_create_cart(db, account=account, session_id=session_id)


@router.get("", response_model=CartResponse)
@router.get("/", response_model=CartResponse, include_in_schema=False)
def get_cart(
    db: Session = Depends(get_db),
    account: models.Account | None = Depends(get_optional_account),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
) -> CartResponse:
    cart = _resolve_cart(db, account, x_session_id)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))


@router.get("/summary", response_model=CartResponse)
def cart_summary(
    db: Session = Depends(get_db),
    account: models.Account | None = Depends(get_optional_account),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
) -> CartResponse:
    cart = _resolve_cart(db, account, x_session_id)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))


@router.post("/items", response_model=CartResponse)
def add_cart_item(
    body: AddItemBody,
    db: Session = Depends(get_db),
    account: models.Account | None = Depends(get_optional_account),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
) -> CartResponse:
    cart = _resolve_cart(db, account, x_session_id)
    svc.add_item(db, cart, product_id=body.product_id, quantity=body.quantity)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))


@router.put("/items/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: int,
    body: UpdateItemBody,
    db: Session = Depends(get_db),
    account: models.Account | None = Depends(get_optional_account),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
) -> CartResponse:
    cart = _resolve_cart(db, account, x_session_id)
    svc.update_item_qty(db, cart, item_id, body.quantity)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))


@router.delete("/items/{item_id}", response_model=CartResponse)
def delete_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    account: models.Account | None = Depends(get_optional_account),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
) -> CartResponse:
    cart = _resolve_cart(db, account, x_session_id)
    svc.remove_item(db, cart, item_id)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))


@router.delete("", response_model=CartResponse)
@router.delete("/", response_model=CartResponse, include_in_schema=False)
def clear_entire_cart(
    db: Session = Depends(get_db),
    account: models.Account | None = Depends(get_optional_account),
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
) -> CartResponse:
    cart = _resolve_cart(db, account, x_session_id)
    svc.clear_cart(db, cart)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))


@router.post("/merge", response_model=CartResponse)
def merge_cart(
    body: MergeBody,
    db: Session = Depends(get_db),
    account: models.Account = Depends(get_current_account),
) -> CartResponse:
    """Merge guest localStorage session cart into the logged-in user's cart."""
    if account.role not in ("customer", "shop_owner", "admin"):
        raise HTTPException(status_code=403, detail="Login required to merge cart")
    cart = svc.merge_guest_into_user(db, account=account, session_id=body.session_id)
    db.commit()
    return CartResponse(**svc.serialize_cart(db, cart))
