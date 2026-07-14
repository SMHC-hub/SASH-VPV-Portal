"""Shop owner APIs — dashboard, shop profile, product CRUD."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db
from backend.deps_auth import require_shop_owner
from backend.shop import owner_service as svc
from backend.shop.owner_service import _utcnow

router = APIRouter(prefix="/api/owner", tags=["shop-owner"])


# ── Schemas ──────────────────────────────────────────────────────────────


class LowStockItem(BaseModel):
    id: int
    name: str
    stock_qty: int
    category: Optional[str] = None


class OwnerDashboardResponse(BaseModel):
    shop_id: int
    shop_name: str
    is_approved: bool
    today_sales_pkr: float
    today_orders: int
    products_listed: int
    products_active: int
    products_pending_approval: int
    low_stock_threshold: int
    low_stock: list[LowStockItem]
    recent_orders: list[dict[str, Any]] = Field(default_factory=list)
    revenue_series: list[dict[str, Any]] = Field(default_factory=list)


class ShopProfileResponse(BaseModel):
    id: int
    owner_user_id: int
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


class ShopProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)


class ProductResponse(BaseModel):
    id: int
    shop_id: int
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


class ProductListResponse(BaseModel):
    count: int
    products: list[ProductResponse]


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    short_desc: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = None
    price_pkr: float = Field(..., gt=0)
    stock_qty: int = Field(default=0, ge=0)
    images: list[Any] = Field(default_factory=list)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    short_desc: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = None
    price_pkr: Optional[float] = Field(default=None, gt=0)
    stock_qty: Optional[int] = Field(default=None, ge=0)
    images: Optional[list[Any]] = None
    is_active: Optional[bool] = None


class DeleteProductResponse(BaseModel):
    success: bool
    deleted_id: int


# ── Routes ───────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=OwnerDashboardResponse)
def owner_dashboard(
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
) -> OwnerDashboardResponse:
    shop = svc.get_owner_shop(db, account)
    return OwnerDashboardResponse(**svc.dashboard_stats(db, shop))


@router.get("/shop", response_model=ShopProfileResponse)
def get_shop_profile(
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
) -> ShopProfileResponse:
    shop = svc.get_owner_shop(db, account)
    return ShopProfileResponse(**svc.serialize_shop(shop))


@router.put("/shop", response_model=ShopProfileResponse)
def update_shop_profile(
    body: ShopProfileUpdate,
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
) -> ShopProfileResponse:
    shop = svc.get_owner_shop(db, account)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] and data["name"] != shop.name:
        shop.name = data["name"].strip()
        shop.slug = svc.unique_shop_slug(db, shop.name, exclude_id=shop.id)
    if "description" in data:
        shop.description = data["description"]
    if "logo_url" in data:
        shop.logo_url = data["logo_url"]
    if "category" in data:
        shop.category = data["category"]
    db.commit()
    db.refresh(shop)
    return ShopProfileResponse(**svc.serialize_shop(shop))


@router.get("/products", response_model=ProductListResponse)
def list_owner_products(
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
    category: Optional[str] = Query(default=None),
    active_only: bool = Query(default=False),
) -> ProductListResponse:
    shop = svc.get_owner_shop(db, account)
    q = select(models.Product).where(models.Product.shop_id == shop.id)
    if category:
        q = q.where(models.Product.category == category)
    if active_only:
        q = q.where(models.Product.is_active.is_(True))
    q = q.order_by(models.Product.created_at.desc())
    products = list(db.execute(q).scalars().all())
    return ProductListResponse(
        count=len(products),
        products=[ProductResponse(**svc.serialize_product(p)) for p in products],
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
) -> ProductResponse:
    shop = svc.get_owner_shop(db, account)
    if not shop.is_approved:
        raise HTTPException(
            status_code=403,
            detail="Shop is not approved yet — wait for admin approval before listing products",
        )
    now = _utcnow()
    product = models.Product(
        shop_id=shop.id,
        name=body.name.strip(),
        slug=svc.unique_product_slug(db, shop, body.name),
        short_desc=body.short_desc,
        description=body.description,
        category=body.category,
        price_pkr=float(body.price_pkr),
        stock_qty=int(body.stock_qty),
        images=list(body.images or []),
        is_active=body.is_active,
        is_approved=False,  # admin must approve (non-negotiable)
        created_at=now,
        updated_at=now,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse(**svc.serialize_product(product))


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
) -> ProductResponse:
    shop = svc.get_owner_shop(db, account)
    product = svc.get_owner_product(db, shop, product_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        product.name = data["name"].strip()
        product.slug = svc.unique_product_slug(db, shop, product.name, exclude_id=product.id)
    for field in ("category", "short_desc", "description", "is_active"):
        if field in data:
            setattr(product, field, data[field])
    if "price_pkr" in data and data["price_pkr"] is not None:
        product.price_pkr = float(data["price_pkr"])
    if "stock_qty" in data and data["stock_qty"] is not None:
        product.stock_qty = int(data["stock_qty"])
    if "images" in data and data["images"] is not None:
        product.images = list(data["images"])
    # Material changes require re-approval
    if any(k in data for k in ("name", "description", "price_pkr", "images")):
        product.is_approved = False
    product.updated_at = _utcnow()
    db.commit()
    db.refresh(product)
    return ProductResponse(**svc.serialize_product(product))


@router.delete("/products/{product_id}", response_model=DeleteProductResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    account: models.Account = Depends(require_shop_owner),
) -> DeleteProductResponse:
    shop = svc.get_owner_shop(db, account)
    product = svc.get_owner_product(db, shop, product_id)
    db.delete(product)
    db.commit()
    return DeleteProductResponse(success=True, deleted_id=product_id)
