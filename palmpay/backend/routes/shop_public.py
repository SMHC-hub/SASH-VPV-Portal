"""Public marketplace catalog — browse products & shops (no auth required)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db

router = APIRouter(prefix="/api/shop", tags=["shop-public"])

SortOption = Literal["newest", "price_asc", "price_desc", "rating", "name"]


class PublicProductCard(BaseModel):
    id: int
    slug: str
    name: str
    short_desc: Optional[str] = None
    category: Optional[str] = None
    price_pkr: float
    stock_qty: int
    stock_status: str
    images: list[Any] = Field(default_factory=list)
    avg_rating: float
    review_count: int
    shop_id: int
    shop_name: str
    shop_slug: str


class PublicProductDetail(PublicProductCard):
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    count: int
    page: int
    limit: int
    total_pages: int
    products: list[PublicProductCard]


class CategoryItem(BaseModel):
    name: str
    product_count: int


class CategoriesResponse(BaseModel):
    count: int
    categories: list[CategoryItem]


class PublicShopCard(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    category: Optional[str] = None
    product_count: int


class ShopListResponse(BaseModel):
    count: int
    shops: list[PublicShopCard]


class PublicShopDetail(PublicShopCard):
    created_at: datetime
    products: list[PublicProductCard] = Field(default_factory=list)


class ReviewsResponse(BaseModel):
    count: int
    page: int
    limit: int
    reviews: list[dict[str, Any]] = Field(default_factory=list)


def _stock_status(qty: int) -> str:
    if qty <= 0:
        return "out_of_stock"
    if qty < 5:
        return "low_stock"
    return "in_stock"


def _visible_product_filters():
    """Only active + approved products from approved shops."""
    return (
        models.Product.is_active.is_(True),
        models.Product.is_approved.is_(True),
        models.Shop.is_approved.is_(True),
    )


def _to_card(product: models.Product, shop: models.Shop) -> PublicProductCard:
    return PublicProductCard(
        id=product.id,
        slug=product.slug,
        name=product.name,
        short_desc=product.short_desc,
        category=product.category,
        price_pkr=product.price_pkr,
        stock_qty=product.stock_qty,
        stock_status=_stock_status(product.stock_qty),
        images=product.images or [],
        avg_rating=product.avg_rating,
        review_count=product.review_count,
        shop_id=shop.id,
        shop_name=shop.name,
        shop_slug=shop.slug,
    )


@router.get("/categories", response_model=CategoriesResponse)
def list_categories(db: Session = Depends(get_db)) -> CategoriesResponse:
    rows = db.execute(
        select(models.Product.category, func.count())
        .join(models.Shop, models.Shop.id == models.Product.shop_id)
        .where(*_visible_product_filters())
        .where(models.Product.category.isnot(None))
        .where(models.Product.category != "")
        .group_by(models.Product.category)
        .order_by(models.Product.category.asc())
    ).all()
    categories = [CategoryItem(name=name, product_count=int(cnt)) for name, cnt in rows if name]
    return CategoriesResponse(count=len(categories), categories=categories)


@router.get("/products", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=120),
    sort: SortOption = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ProductListResponse:
    base = (
        select(models.Product, models.Shop)
        .join(models.Shop, models.Shop.id == models.Product.shop_id)
        .where(*_visible_product_filters())
    )
    if category:
        base = base.where(models.Product.category == category)
    if search:
        q = f"%{search.strip()}%"
        base = base.where(
            or_(
                models.Product.name.ilike(q),
                models.Product.short_desc.ilike(q),
                models.Product.description.ilike(q),
                models.Shop.name.ilike(q),
            )
        )

    count_q = select(func.count()).select_from(base.subquery())
    total = int(db.execute(count_q).scalar_one() or 0)

    if sort == "price_asc":
        base = base.order_by(models.Product.price_pkr.asc())
    elif sort == "price_desc":
        base = base.order_by(models.Product.price_pkr.desc())
    elif sort == "rating":
        base = base.order_by(models.Product.avg_rating.desc(), models.Product.review_count.desc())
    elif sort == "name":
        base = base.order_by(models.Product.name.asc())
    else:
        base = base.order_by(models.Product.created_at.desc())

    offset = (page - 1) * limit
    rows = db.execute(base.offset(offset).limit(limit)).all()
    products = [_to_card(p, s) for p, s in rows]
    total_pages = max(1, (total + limit - 1) // limit) if total else 0
    return ProductListResponse(
        count=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        products=products,
    )


@router.get("/products/{slug}", response_model=PublicProductDetail)
def get_product(slug: str, db: Session = Depends(get_db)) -> PublicProductDetail:
    row = db.execute(
        select(models.Product, models.Shop)
        .join(models.Shop, models.Shop.id == models.Product.shop_id)
        .where(models.Product.slug == slug)
        .where(*_visible_product_filters())
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product, shop = row
    card = _to_card(product, shop)
    return PublicProductDetail(
        **card.model_dump(),
        description=product.description,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("/products/{product_id}/reviews", response_model=ReviewsResponse)
def list_product_reviews(
    product_id: int,
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ReviewsResponse:
    """Reviews table lands in a later TODO — empty list for now."""
    product = db.execute(
        select(models.Product)
        .join(models.Shop, models.Shop.id == models.Product.shop_id)
        .where(models.Product.id == product_id)
        .where(*_visible_product_filters())
    ).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ReviewsResponse(count=0, page=page, limit=limit, reviews=[])


@router.get("/shops", response_model=ShopListResponse)
def list_shops(db: Session = Depends(get_db)) -> ShopListResponse:
    shops = list(
        db.execute(
            select(models.Shop)
            .where(models.Shop.is_approved.is_(True))
            .order_by(models.Shop.name.asc())
        ).scalars().all()
    )
    items: list[PublicShopCard] = []
    for shop in shops:
        cnt = int(
            db.execute(
                select(func.count())
                .select_from(models.Product)
                .where(
                    models.Product.shop_id == shop.id,
                    models.Product.is_active.is_(True),
                    models.Product.is_approved.is_(True),
                )
            ).scalar_one()
            or 0
        )
        items.append(
            PublicShopCard(
                id=shop.id,
                name=shop.name,
                slug=shop.slug,
                description=shop.description,
                logo_url=shop.logo_url,
                category=shop.category,
                product_count=cnt,
            )
        )
    return ShopListResponse(count=len(items), shops=items)


@router.get("/shops/{slug}", response_model=PublicShopDetail)
def get_shop(slug: str, db: Session = Depends(get_db)) -> PublicShopDetail:
    shop = db.execute(
        select(models.Shop)
        .where(models.Shop.slug == slug, models.Shop.is_approved.is_(True))
    ).scalar_one_or_none()
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")

    products = list(
        db.execute(
            select(models.Product)
            .where(
                models.Product.shop_id == shop.id,
                models.Product.is_active.is_(True),
                models.Product.is_approved.is_(True),
            )
            .order_by(models.Product.created_at.desc())
        ).scalars().all()
    )
    cards = [_to_card(p, shop) for p in products]
    return PublicShopDetail(
        id=shop.id,
        name=shop.name,
        slug=shop.slug,
        description=shop.description,
        logo_url=shop.logo_url,
        category=shop.category,
        product_count=len(cards),
        created_at=shop.created_at,
        products=cards,
    )
