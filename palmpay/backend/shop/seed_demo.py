"""Seed an approved demo shop + sample products for development."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.passwords import hash_password
from backend.db import models
from backend.shop.identity_link import DEMO_SHOP_OWNER_PHONE, ensure_palmpay_link_for_account

logger = logging.getLogger(__name__)

DEMO_SHOP_SLUG = "veinpay-demo-mart"
DEMO_OWNER_EMAIL = "demo-shop@example.com"
DEMO_OWNER_PASSWORD = "DemoShop123!"
DEMO_OWNER_DATASET_ID = "SHOP01"
DEMO_OWNER_DATASET_NAME = "DemoShopOwner"
_LEGACY_OWNER_EMAILS = ("demo-shop@veinpay.local",)

# Section 11 sample catalog (Pakistan PKR pricing) + public image filenames
DEMO_PRODUCTS: list[dict] = [
    {"name": "USB-C Charging Cable (2m)", "category": "Electronics", "price_pkr": 450, "stock_qty": 100, "image": "usb-c-charging-cable.png"},
    {"name": "Wireless Earbuds (Basic)", "category": "Electronics", "price_pkr": 2800, "stock_qty": 30, "image": "wireless-earbuds.png"},
    {"name": "Phone Screen Protector", "category": "Electronics", "price_pkr": 350, "stock_qty": 200, "image": "screen-protector.png"},
    {"name": "Power Bank 10,000mAh", "category": "Electronics", "price_pkr": 3200, "stock_qty": 25, "image": "power-bank.png"},
    {"name": "LED Desk Lamp", "category": "Electronics", "price_pkr": 1200, "stock_qty": 40, "image": "led-desk-lamp.png"},
    {"name": "Men's Cotton T-Shirt", "category": "Clothing", "price_pkr": 890, "stock_qty": 80, "image": "mens-tshirt.png"},
    {"name": "Women's Lawn Dupatta", "category": "Clothing", "price_pkr": 1500, "stock_qty": 50, "image": "lawn-dupatta.png"},
    {"name": "Sports Shorts", "category": "Clothing", "price_pkr": 1100, "stock_qty": 60, "image": "sports-shorts.png"},
    {"name": "Winter Socks (Pack of 3)", "category": "Clothing", "price_pkr": 550, "stock_qty": 150, "image": "winter-socks.png"},
    {"name": "Casual Sneakers (Size 40-45)", "category": "Clothing", "price_pkr": 4500, "stock_qty": 20, "image": "casual-sneakers.png"},
    {"name": "Himalayan Pink Salt 1kg", "category": "Food & Groceries", "price_pkr": 280, "stock_qty": 500, "image": "pink-salt.png"},
    {"name": "Green Tea (50 bags)", "category": "Food & Groceries", "price_pkr": 420, "stock_qty": 200, "image": "green-tea.png"},
    {"name": "Mixed Dry Fruits 500g", "category": "Food & Groceries", "price_pkr": 1800, "stock_qty": 75, "image": "dry-fruits.png"},
    {"name": "Organic Honey 500ml", "category": "Food & Groceries", "price_pkr": 950, "stock_qty": 100, "image": "organic-honey.png"},
    {"name": "Basmati Rice 5kg", "category": "Food & Groceries", "price_pkr": 1650, "stock_qty": 300, "image": "basmati-rice.png"},
    {"name": "Atomic Habits (Urdu Edition)", "category": "Books", "price_pkr": 750, "stock_qty": 40, "image": "atomic-habits.png"},
    {"name": "The Alchemist (English)", "category": "Books", "price_pkr": 650, "stock_qty": 35, "image": "the-alchemist.png"},
    {"name": "CSS/PMS Guide 2024", "category": "Books", "price_pkr": 1200, "stock_qty": 60, "image": "css-guide.png"},
    {"name": "Learn Python in 30 Days", "category": "Books", "price_pkr": 850, "stock_qty": 45, "image": "python-book.png"},
    {"name": "Islamic Calligraphy Workbook", "category": "Books", "price_pkr": 480, "stock_qty": 80, "image": "calligraphy-workbook.png"},
    {"name": "Ceramic Coffee Mug", "category": "Home & Living", "price_pkr": 380, "stock_qty": 120, "image": "coffee-mug.png"},
    {"name": "Bamboo Cutting Board", "category": "Home & Living", "price_pkr": 650, "stock_qty": 90, "image": "bamboo-board.png"},
    {"name": "Scented Candle Set (3pc)", "category": "Home & Living", "price_pkr": 1100, "stock_qty": 60, "image": "candle-set.png"},
    {"name": "Storage Basket (Large)", "category": "Home & Living", "price_pkr": 780, "stock_qty": 70, "image": "storage-basket.png"},
    {"name": "Digital Kitchen Scale", "category": "Home & Living", "price_pkr": 1400, "stock_qty": 45, "image": "kitchen-scale.png"},
]


def product_images_payload(filename: str | None) -> list[dict]:
    if not filename:
        return []
    return [{"url": f"/shop-images/{filename}", "order": 0, "is_primary": True}]


def slugify(value: str) -> str:
    s = value.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:200] or "item"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _migrate_demo_owner_email(db: Session) -> models.Account | None:
    owner = db.execute(
        select(models.Account).where(models.Account.email == DEMO_OWNER_EMAIL)
    ).scalar_one_or_none()
    if owner is not None:
        return owner
    for legacy in _LEGACY_OWNER_EMAILS:
        legacy_acc = db.execute(
            select(models.Account).where(models.Account.email == legacy)
        ).scalar_one_or_none()
        if legacy_acc is not None:
            legacy_acc.email = DEMO_OWNER_EMAIL
            if legacy_acc.role != "shop_owner":
                legacy_acc.role = "shop_owner"
            db.commit()
            db.refresh(legacy_acc)
            logger.info("Migrated demo shop owner email %s → %s", legacy, DEMO_OWNER_EMAIL)
            return legacy_acc
    return None


def ensure_demo_shop(db: Session) -> models.Shop:
    """Create approved demo shop + catalog if missing. Idempotent."""
    _migrate_demo_owner_email(db)

    existing = db.execute(
        select(models.Shop).where(models.Shop.slug == DEMO_SHOP_SLUG)
    ).scalar_one_or_none()
    if existing:
        product_count = db.execute(
            select(models.Product).where(models.Product.shop_id == existing.id).limit(1)
        ).scalar_one_or_none()
        if product_count is None:
            _seed_products(db, existing)
            db.commit()
            db.refresh(existing)
        else:
            n = sync_demo_product_images(db, existing)
            if n:
                db.commit()
                logger.info("Synced images onto %s demo products", n)
        return existing

    owner = _migrate_demo_owner_email(db)
    if owner is None:
        # Avoid dataset_id collision with live enrollments
        taken = db.execute(
            select(models.Account).where(models.Account.dataset_id == DEMO_OWNER_DATASET_ID)
        ).scalar_one_or_none()
        dataset_id = DEMO_OWNER_DATASET_ID if taken is None else "SHPDEMO"
        owner = models.Account(
            email=DEMO_OWNER_EMAIL,
            password_hash=hash_password(DEMO_OWNER_PASSWORD),
            full_name="Demo Shop Owner",
            dataset_id=dataset_id,
            dataset_name=DEMO_OWNER_DATASET_NAME,
            role="shop_owner",
            email_verified=True,
        )
        db.add(owner)
        db.flush()
    elif owner.role != "shop_owner":
        owner.role = "shop_owner"

    admin = db.execute(
        select(models.Account).where(models.Account.role == "admin").order_by(models.Account.id)
    ).scalar_one_or_none()

    shop = models.Shop(
        owner_user_id=owner.id,
        name="VeinPay Demo Mart",
        slug=DEMO_SHOP_SLUG,
        description="Demo marketplace shop for palm-vein checkout development.",
        category="General",
        commission_rate=0.05,
        is_approved=True,
        approved_by=admin.id if admin else owner.id,
        approved_at=_utcnow(),
    )
    db.add(shop)
    db.flush()
    _seed_products(db, shop)
    db.commit()
    db.refresh(shop)
    logger.info(
        "Seeded demo shop '%s' with %s products (owner=%s)",
        shop.name,
        len(DEMO_PRODUCTS),
        DEMO_OWNER_EMAIL,
    )
    return shop


def _seed_products(db: Session, shop: models.Shop) -> None:
    now = _utcnow()
    for item in DEMO_PRODUCTS:
        slug = f"{shop.slug}-{slugify(item['name'])}"
        exists = db.execute(
            select(models.Product).where(models.Product.slug == slug)
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            models.Product(
                shop_id=shop.id,
                name=item["name"],
                slug=slug,
                short_desc=item["name"],
                description=item["name"],
                category=item["category"],
                price_pkr=float(item["price_pkr"]),
                stock_qty=int(item["stock_qty"]),
                images=product_images_payload(item.get("image")),
                avg_rating=4.0,
                review_count=0,
                is_active=True,
                is_approved=True,
                created_at=now,
                updated_at=now,
            )
        )


def sync_demo_product_images(db: Session, shop: models.Shop | None = None) -> int:
    """Attach / refresh catalog images on demo products. Returns updated row count."""
    if shop is None:
        shop = db.execute(
            select(models.Shop).where(models.Shop.slug == DEMO_SHOP_SLUG)
        ).scalar_one_or_none()
    if shop is None:
        return 0
    updated = 0
    for item in DEMO_PRODUCTS:
        slug = f"{shop.slug}-{slugify(item['name'])}"
        product = db.execute(
            select(models.Product).where(models.Product.slug == slug)
        ).scalar_one_or_none()
        if product is None:
            continue
        payload = product_images_payload(item.get("image"))
        if product.images != payload:
            product.images = payload
            product.updated_at = _utcnow()
            updated += 1
    return updated


def ensure_demo_shop_wallet_link(db: Session) -> models.Shop | None:
    """Ensure demo shop owner has a VeinPay wallet and shop.wallet_id is set."""
    shop = db.execute(
        select(models.Shop).where(models.Shop.slug == DEMO_SHOP_SLUG)
    ).scalar_one_or_none()
    if shop is None:
        return None

    owner = db.get(models.Account, shop.owner_user_id)
    if owner is None:
        return shop

    _pp, wallet = ensure_palmpay_link_for_account(
        db, owner, phone=DEMO_SHOP_OWNER_PHONE, commit=False
    )
    if shop.wallet_id != wallet.id:
        shop.wallet_id = wallet.id
    db.commit()
    db.refresh(shop)
    logger.info(
        "Demo shop wallet linked shop_id=%s wallet_id=%s palmpay_account_id=%s",
        shop.id,
        shop.wallet_id,
        owner.palmpay_account_id,
    )
    return shop
