"""Shop-owner domain helpers (profile + products)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db import models
from backend.shop.seed_demo import slugify

LOW_STOCK_THRESHOLD = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_owner_shop(db: Session, owner: models.Account) -> models.Shop:
    shop = db.execute(
        select(models.Shop)
        .where(models.Shop.owner_user_id == owner.id)
        .order_by(models.Shop.id)
    ).scalars().first()
    if shop is None:
        raise HTTPException(status_code=404, detail="No shop registered for this account")
    return shop


def unique_product_slug(db: Session, shop: models.Shop, name: str, *, exclude_id: int | None = None) -> str:
    base = f"{shop.slug}-{slugify(name)}"
    candidate = base
    n = 2
    while True:
        q = select(models.Product).where(models.Product.slug == candidate)
        if exclude_id is not None:
            q = q.where(models.Product.id != exclude_id)
        exists = db.execute(q).scalar_one_or_none()
        if exists is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def unique_shop_slug(db: Session, name: str, *, exclude_id: int | None = None) -> str:
    base = slugify(name)
    candidate = base
    n = 2
    while True:
        q = select(models.Shop).where(models.Shop.slug == candidate)
        if exclude_id is not None:
            q = q.where(models.Shop.id != exclude_id)
        exists = db.execute(q).scalar_one_or_none()
        if exists is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def get_owner_product(db: Session, shop: models.Shop, product_id: int) -> models.Product:
    product = db.get(models.Product, product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def dashboard_stats(db: Session, shop: models.Shop) -> dict:
    product_count = db.execute(
        select(func.count()).select_from(models.Product).where(models.Product.shop_id == shop.id)
    ).scalar_one()
    active_count = db.execute(
        select(func.count())
        .select_from(models.Product)
        .where(models.Product.shop_id == shop.id, models.Product.is_active.is_(True))
    ).scalar_one()
    pending_count = db.execute(
        select(func.count())
        .select_from(models.Product)
        .where(
            models.Product.shop_id == shop.id,
            models.Product.is_approved.is_(False),
        )
    ).scalar_one()
    low_stock = list(
        db.execute(
            select(models.Product)
            .where(
                models.Product.shop_id == shop.id,
                models.Product.stock_qty < LOW_STOCK_THRESHOLD,
                models.Product.is_active.is_(True),
            )
            .order_by(models.Product.stock_qty.asc())
            .limit(20)
        ).scalars().all()
    )
    return {
        "shop_id": shop.id,
        "shop_name": shop.name,
        "is_approved": shop.is_approved,
        "today_sales_pkr": 0.0,
        "today_orders": 0,
        "products_listed": int(product_count or 0),
        "products_active": int(active_count or 0),
        "products_pending_approval": int(pending_count or 0),
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        "low_stock": [
            {
                "id": p.id,
                "name": p.name,
                "stock_qty": p.stock_qty,
                "category": p.category,
            }
            for p in low_stock
        ],
        "recent_orders": [],
        "revenue_series": [],
    }


def serialize_shop(shop: models.Shop) -> dict:
    return {
        "id": shop.id,
        "owner_user_id": shop.owner_user_id,
        "name": shop.name,
        "slug": shop.slug,
        "description": shop.description,
        "logo_url": shop.logo_url,
        "category": shop.category,
        "commission_rate": shop.commission_rate,
        "is_approved": shop.is_approved,
        "approved_at": shop.approved_at,
        "rejection_reason": shop.rejection_reason,
        "wallet_id": shop.wallet_id,
        "created_at": shop.created_at,
    }


def serialize_product(product: models.Product) -> dict:
    return {
        "id": product.id,
        "shop_id": product.shop_id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "short_desc": product.short_desc,
        "category": product.category,
        "price_pkr": product.price_pkr,
        "stock_qty": product.stock_qty,
        "images": product.images or [],
        "avg_rating": product.avg_rating,
        "review_count": product.review_count,
        "is_active": product.is_active,
        "is_approved": product.is_approved,
        "rejection_reason": product.rejection_reason,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
