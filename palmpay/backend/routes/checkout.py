"""Checkout APIs — validate, initiate, palm-pay, cancel."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db
from backend.deps_auth import require_customer
from backend.shop import checkout_service as svc

router = APIRouter(prefix="/api/checkout", tags=["checkout"])


class ValidateResponse(BaseModel):
    logged_in: bool
    palm_enrolled: bool
    balance_sufficient: bool
    wallet_balance: float
    cart_total: float
    shortfall: Optional[float] = None
    action_required: str
    item_count: int
    warnings: list[str] = Field(default_factory=list)


class OrderItemOut(BaseModel):
    id: int
    product_id: Optional[int] = None
    shop_id: Optional[int] = None
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    shop_earnings: float
    platform_take: float


class InitiateResponse(BaseModel):
    order_id: int
    order_number: str
    status: str
    payment_status: str
    subtotal_pkr: float
    platform_fee_pkr: float
    total_pkr: float
    expires_at: datetime
    items_summary: list[dict[str, Any]]
    confidence_required: float = svc.SHOP_PALM_CONFIDENCE_MIN


class PalmPayBody(BaseModel):
    order_id: int
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    scan_event_id: Optional[str] = None


class PalmPayResponse(BaseModel):
    success: bool
    already_paid: bool = False
    order_id: int
    order_number: str
    status: str
    payment_status: str
    total_pkr: float
    subtotal_pkr: float
    platform_fee_pkr: float
    palm_confidence: Optional[float] = None
    transaction_id: Optional[int] = None
    new_balance_pkr: Optional[float] = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    message: str


class CancelResponse(BaseModel):
    success: bool
    order_id: int
    status: str
    message: str


@router.post("/validate", response_model=ValidateResponse)
def checkout_validate(
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_customer),
) -> ValidateResponse:
    data = svc.validate_checkout(db, account)
    db.commit()
    return ValidateResponse(**data)


@router.post("/initiate", response_model=InitiateResponse)
def checkout_initiate(
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_customer),
) -> InitiateResponse:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    order = svc.initiate_checkout(db, account)
    db.commit()
    order = db.execute(
        select(models.ShopOrder)
        .where(models.ShopOrder.id == order.id)
        .options(selectinload(models.ShopOrder.items))
    ).scalar_one()
    return InitiateResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        payment_status=order.payment_status,
        subtotal_pkr=order.subtotal_pkr,
        platform_fee_pkr=order.platform_fee_pkr,
        total_pkr=order.total_pkr,
        expires_at=order.expires_at,
        items_summary=[
            {
                "product_name": i.product_name,
                "quantity": i.quantity,
                "line_total": i.line_total,
                "shop_id": i.shop_id,
            }
            for i in order.items
        ],
    )


@router.post("/palm-pay", response_model=PalmPayResponse)
def checkout_palm_pay(
    body: PalmPayBody,
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_customer),
) -> PalmPayResponse:
    try:
        result = svc.palm_pay_order(
            db,
            account,
            order_id=body.order_id,
            confidence=body.confidence,
            scan_event_id=body.scan_event_id,
        )
        db.commit()
        return PalmPayResponse(**result)
    except HTTPException:
        # Persist scan attempts / auto-cancel even on failure
        db.commit()
        raise


@router.post("/cancel/{order_id}", response_model=CancelResponse)
def checkout_cancel(
    order_id: int,
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_customer),
) -> CancelResponse:
    order = svc.cancel_checkout(db, account, order_id)
    db.commit()
    return CancelResponse(
        success=True,
        order_id=order.id,
        status=order.status,
        message="Order cancelled — stock released",
    )
