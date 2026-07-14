"""Admin marketplace moderation — shops & products approve/reject."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db
from backend.deps_auth import get_current_account
from backend.shop.owner_service import serialize_product, serialize_shop

router = APIRouter(prefix="/api/admin", tags=["admin-shop"])


def require_admin(account: models.Account = Depends(get_current_account)) -> models.Account:
    if account.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return account


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RejectBody(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class AdminShopItem(BaseModel):
    id: int
    owner_user_id: int
    owner_email: Optional[str] = None
    owner_name: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    category: Optional[str] = None
    commission_rate: float
    is_approved: bool
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    wallet_id: Optional[int] = None
    created_at: datetime
    product_count: int = 0


class AdminShopListResponse(BaseModel):
    count: int
    shops: list[AdminShopItem]


class AdminProductItem(BaseModel):
    id: int
    shop_id: int
    shop_name: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    short_desc: Optional[str] = None
    category: Optional[str] = None
    price_pkr: float
    stock_qty: int
    images: list[Any] = Field(default_factory=list)
    avg_rating: float
    review_count: int
    is_active: bool
    is_approved: bool
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminProductListResponse(BaseModel):
    count: int
    products: list[AdminProductItem]


class ModerationActionResponse(BaseModel):
    success: bool
    id: int
    is_approved: bool
    rejection_reason: Optional[str] = None
    message: str


def _shop_item(db: Session, shop: models.Shop) -> AdminShopItem:
    from sqlalchemy import func

    owner = db.get(models.Account, shop.owner_user_id)
    product_count = int(
        db.execute(
            select(func.count())
            .select_from(models.Product)
            .where(models.Product.shop_id == shop.id)
        ).scalar_one()
        or 0
    )
    base = serialize_shop(shop)
    return AdminShopItem(
        **base,
        owner_email=owner.email if owner else None,
        owner_name=owner.full_name if owner else None,
        product_count=product_count,
    )


def _product_item(db: Session, product: models.Product) -> AdminProductItem:
    shop = db.get(models.Shop, product.shop_id)
    base = serialize_product(product)
    return AdminProductItem(
        **base,
        shop_name=shop.name if shop else None,
    )


@router.get("/shops/pending", response_model=AdminShopListResponse)
def list_pending_shops(
    db: Session = Depends(get_db),
    _: models.Account = Depends(require_admin),
) -> AdminShopListResponse:
    shops = list(
        db.execute(
            select(models.Shop)
            .where(models.Shop.is_approved.is_(False))
            .order_by(models.Shop.created_at.asc())
        ).scalars().all()
    )
    return AdminShopListResponse(
        count=len(shops),
        shops=[_shop_item(db, s) for s in shops],
    )


@router.get("/shops", response_model=AdminShopListResponse)
def list_all_shops(
    db: Session = Depends(get_db),
    _: models.Account = Depends(require_admin),
    approved: Optional[bool] = Query(default=None),
) -> AdminShopListResponse:
    q = select(models.Shop).order_by(models.Shop.created_at.desc())
    if approved is not None:
        q = q.where(models.Shop.is_approved.is_(approved))
    shops = list(db.execute(q).scalars().all())
    return AdminShopListResponse(
        count=len(shops),
        shops=[_shop_item(db, s) for s in shops],
    )


@router.post("/shops/{shop_id}/approve", response_model=ModerationActionResponse)
def approve_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(require_admin),
) -> ModerationActionResponse:
    shop = db.get(models.Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.is_approved = True
    shop.approved_by = admin.id
    shop.approved_at = _utcnow()
    shop.rejection_reason = None
    db.commit()
    return ModerationActionResponse(
        success=True,
        id=shop.id,
        is_approved=True,
        rejection_reason=None,
        message=f"Shop '{shop.name}' approved",
    )


@router.post("/shops/{shop_id}/reject", response_model=ModerationActionResponse)
def reject_shop(
    shop_id: int,
    body: RejectBody,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(require_admin),
) -> ModerationActionResponse:
    shop = db.get(models.Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.is_approved = False
    shop.approved_by = None
    shop.approved_at = None
    shop.rejection_reason = body.reason.strip()
    # Hide all products while shop is rejected
    for p in db.execute(
        select(models.Product).where(models.Product.shop_id == shop.id)
    ).scalars().all():
        p.is_active = False
    db.commit()
    return ModerationActionResponse(
        success=True,
        id=shop.id,
        is_approved=False,
        rejection_reason=shop.rejection_reason,
        message=f"Shop '{shop.name}' rejected",
    )


@router.get("/products/pending", response_model=AdminProductListResponse)
def list_pending_products(
    db: Session = Depends(get_db),
    _: models.Account = Depends(require_admin),
) -> AdminProductListResponse:
    products = list(
        db.execute(
            select(models.Product)
            .where(models.Product.is_approved.is_(False))
            .order_by(models.Product.created_at.asc())
        ).scalars().all()
    )
    return AdminProductListResponse(
        count=len(products),
        products=[_product_item(db, p) for p in products],
    )


@router.get("/products", response_model=AdminProductListResponse)
def list_all_products(
    db: Session = Depends(get_db),
    _: models.Account = Depends(require_admin),
    approved: Optional[bool] = Query(default=None),
    shop_id: Optional[int] = Query(default=None),
) -> AdminProductListResponse:
    q = select(models.Product).order_by(models.Product.created_at.desc())
    if approved is not None:
        q = q.where(models.Product.is_approved.is_(approved))
    if shop_id is not None:
        q = q.where(models.Product.shop_id == shop_id)
    products = list(db.execute(q).scalars().all())
    return AdminProductListResponse(
        count=len(products),
        products=[_product_item(db, p) for p in products],
    )


@router.post("/products/{product_id}/approve", response_model=ModerationActionResponse)
def approve_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(require_admin),
) -> ModerationActionResponse:
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    shop = db.get(models.Shop, product.shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    if not shop.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve product while its shop is not approved",
        )
    # Non-negotiable: shop owner cannot approve own products (admin-only route)
    if shop.owner_user_id == admin.id:
        raise HTTPException(
            status_code=403,
            detail="Shop owner cannot approve their own products",
        )
    product.is_approved = True
    product.rejection_reason = None
    product.updated_at = _utcnow()
    db.commit()
    return ModerationActionResponse(
        success=True,
        id=product.id,
        is_approved=True,
        rejection_reason=None,
        message=f"Product '{product.name}' approved",
    )


@router.post("/products/{product_id}/reject", response_model=ModerationActionResponse)
def reject_product(
    product_id: int,
    body: RejectBody,
    db: Session = Depends(get_db),
    _: models.Account = Depends(require_admin),
) -> ModerationActionResponse:
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_approved = False
    product.is_active = False
    product.rejection_reason = body.reason.strip()
    product.updated_at = _utcnow()
    db.commit()
    return ModerationActionResponse(
        success=True,
        id=product.id,
        is_approved=False,
        rejection_reason=product.rejection_reason,
        message=f"Product '{product.name}' rejected",
    )
