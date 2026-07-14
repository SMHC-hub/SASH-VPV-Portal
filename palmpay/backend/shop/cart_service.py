"""Cart domain — guest session carts + authenticated user carts."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.db import models

PLATFORM_FEE_PKR = 0.0  # configurable later via admin settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _load_product(db: Session, product_id: int) -> models.Product:
    product = db.execute(
        select(models.Product)
        .join(models.Shop, models.Shop.id == models.Product.shop_id)
        .where(models.Product.id == product_id)
        .where(models.Product.is_active.is_(True))
        .where(models.Product.is_approved.is_(True))
        .where(models.Shop.is_approved.is_(True))
    ).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not available")
    return product


def get_or_create_cart(
    db: Session,
    *,
    account: models.Account | None,
    session_id: str | None,
) -> models.Cart:
    if account is not None:
        cart = db.execute(
            select(models.Cart)
            .where(models.Cart.user_id == account.id)
            .options(selectinload(models.Cart.items).selectinload(models.CartItem.product))
        ).scalar_one_or_none()
        if cart is None:
            cart = models.Cart(user_id=account.id, session_id=None)
            db.add(cart)
            db.flush()
        return cart

    if not session_id or not session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Guest cart requires X-Session-Id header",
        )
    sid = session_id.strip()[:255]
    cart = db.execute(
        select(models.Cart)
        .where(models.Cart.session_id == sid)
        .options(selectinload(models.Cart.items).selectinload(models.CartItem.product))
    ).scalar_one_or_none()
    if cart is None:
        cart = models.Cart(user_id=None, session_id=sid)
        db.add(cart)
        db.flush()
    return cart


def find_cart_item(cart: models.Cart, item_id: int) -> models.CartItem:
    for item in cart.items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Cart item not found")


def add_item(
    db: Session,
    cart: models.Cart,
    *,
    product_id: int,
    quantity: int,
) -> models.CartItem:
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    product = _load_product(db, product_id)
    if product.stock_qty < 1:
        raise HTTPException(status_code=400, detail="Product is out of stock")

    existing = next((i for i in cart.items if i.product_id == product_id), None)
    if existing:
        new_qty = existing.quantity + quantity
        if new_qty > product.stock_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock_qty} in stock",
            )
        existing.quantity = new_qty
        existing.price_at_add = float(product.price_pkr)
        cart.updated_at = _utcnow()
        db.flush()
        return existing

    if quantity > product.stock_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock_qty} in stock",
        )
    item = models.CartItem(
        cart_id=cart.id,
        product_id=product.id,
        quantity=quantity,
        price_at_add=float(product.price_pkr),
        added_at=_utcnow(),
    )
    db.add(item)
    cart.updated_at = _utcnow()
    db.flush()
    return item


def update_item_qty(db: Session, cart: models.Cart, item_id: int, quantity: int) -> models.CartItem:
    item = find_cart_item(cart, item_id)
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    product = db.get(models.Product, item.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product no longer exists")
    if quantity > product.stock_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock_qty} in stock",
        )
    item.quantity = quantity
    cart.updated_at = _utcnow()
    db.flush()
    return item


def remove_item(db: Session, cart: models.Cart, item_id: int) -> None:
    item = find_cart_item(cart, item_id)
    db.delete(item)
    cart.updated_at = _utcnow()
    db.flush()


def clear_cart(db: Session, cart: models.Cart) -> None:
    for item in list(cart.items):
        db.delete(item)
    cart.updated_at = _utcnow()
    db.flush()


def merge_guest_into_user(
    db: Session,
    *,
    account: models.Account,
    session_id: str,
) -> models.Cart:
    """Merge guest session cart into the user's persistent cart."""
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id required")
    sid = session_id.strip()[:255]

    user_cart = get_or_create_cart(db, account=account, session_id=None)
    guest = db.execute(
        select(models.Cart)
        .where(models.Cart.session_id == sid)
        .options(selectinload(models.Cart.items))
    ).scalar_one_or_none()
    if guest is None or guest.id == user_cart.id:
        return user_cart

    # Snapshot guest lines first — deleting the guest cart cascades items
    pending: list[tuple[int, int]] = [
        (g_item.product_id, g_item.quantity) for g_item in list(guest.items)
    ]
    db.delete(guest)
    db.flush()

    for product_id, quantity in pending:
        try:
            add_item(db, user_cart, product_id=product_id, quantity=quantity)
        except HTTPException:
            # Skip unavailable / overstock lines during merge
            continue

    user_cart.updated_at = _utcnow()
    db.flush()
    return get_or_create_cart(db, account=account, session_id=None)


def serialize_cart(db: Session, cart: models.Cart) -> dict:
    warnings: list[str] = []
    items_out: list[dict] = []
    subtotal = 0.0
    item_count = 0

    # Refresh items with products
    cart = db.execute(
        select(models.Cart)
        .where(models.Cart.id == cart.id)
        .options(selectinload(models.Cart.items).selectinload(models.CartItem.product))
    ).scalar_one()

    for item in cart.items:
        product = item.product or db.get(models.Product, item.product_id)
        if product is None:
            warnings.append(f"Item {item.id} removed — product missing")
            continue
        shop = db.get(models.Shop, product.shop_id)
        current_price = float(product.price_pkr)
        if abs(current_price - float(item.price_at_add)) > 0.009:
            warnings.append(
                f"Price of {product.name} changed from PKR {item.price_at_add:,.0f} "
                f"to PKR {current_price:,.0f}"
            )
        if product.stock_qty <= 0 or not product.is_active or not product.is_approved:
            warnings.append(f"Item {product.name} is now out of stock. Remove to continue.")
        elif item.quantity > product.stock_qty:
            warnings.append(
                f"Only {product.stock_qty} of {product.name} left (you have {item.quantity})"
            )

        line_total = current_price * item.quantity
        subtotal += line_total
        item_count += item.quantity
        images = product.images or []
        items_out.append(
            {
                "id": item.id,
                "product_id": product.id,
                "product_slug": product.slug,
                "name": product.name,
                "image_url": images[0].get("url") if images and isinstance(images[0], dict) else None,
                "quantity": item.quantity,
                "unit_price": current_price,
                "price_at_add": float(item.price_at_add),
                "line_total": line_total,
                "stock_qty": product.stock_qty,
                "shop_id": product.shop_id,
                "shop_name": shop.name if shop else None,
            }
        )

    platform_fee = PLATFORM_FEE_PKR
    return {
        "cart_id": cart.id,
        "user_id": cart.user_id,
        "session_id": cart.session_id,
        "item_count": item_count,
        "items": items_out,
        "subtotal_pkr": round(subtotal, 2),
        "platform_fee_pkr": platform_fee,
        "total_pkr": round(subtotal + platform_fee, 2),
        "warnings": warnings,
        "updated_at": cart.updated_at,
    }
