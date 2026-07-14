"""Checkout + palm-pay for marketplace orders (commission split)."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.db import models
from backend.shop.cart_service import PLATFORM_FEE_PKR, clear_cart, get_or_create_cart, serialize_cart
from backend.shop.identity_link import get_linked_wallet, resolve_or_link_palmpay_by_email
from backend.utils.wallet_cache import invalidate_wallet_cache
from backend.wallet.palmpay_wallet_service import _new_ref, _write_ledger, get_or_create_wallet

logger = logging.getLogger(__name__)

# Non-negotiable: payment palm match must be ≥ 97%
SHOP_PALM_CONFIDENCE_MIN = 0.97
ORDER_LOCK_TTL_MINUTES = 15
MAX_SCAN_ATTEMPTS = 3

PLATFORM_PHONE = "03000000001"
PLATFORM_EMAIL = "platform@veinpay.local"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_platform_wallet(db: Session) -> tuple[models.PalmPayAccount, models.PalmPayWallet]:
    pp = db.execute(
        select(models.PalmPayAccount).where(models.PalmPayAccount.phone == PLATFORM_PHONE)
    ).scalar_one_or_none()
    if pp is None:
        pp = models.PalmPayAccount(
            phone=PLATFORM_PHONE,
            email=PLATFORM_EMAIL,
            full_name="VeinPay Platform",
            kyc_status="verified",
            email_verified=True,
            phone_verified=True,
        )
        db.add(pp)
        db.flush()
    wallet = get_or_create_wallet(db, pp)
    return pp, wallet


def _new_order_number() -> str:
    stamp = _utcnow().strftime("%Y%m%d")
    return f"ORD-{stamp}-{secrets.token_hex(3).upper()}"


def _palm_enrolled(account: models.Account) -> bool:
    return account.left_template is not None or account.right_template is not None


def expire_stale_orders(db: Session, customer_id: int | None = None) -> int:
    """Release stock for expired pending orders. Returns count expired."""
    q = select(models.ShopOrder).where(
        models.ShopOrder.status == "pending",
        models.ShopOrder.expires_at < _utcnow(),
    )
    if customer_id is not None:
        q = q.where(models.ShopOrder.customer_id == customer_id)
    expired = list(db.execute(q.options(selectinload(models.ShopOrder.items))).scalars().all())
    for order in expired:
        _release_stock(db, order)
        order.status = "expired"
        order.payment_status = "failed"
        order.stock_locked = False
        order.updated_at = _utcnow()
        order.notes = (order.notes or "") + " | auto-expired"
    if expired:
        db.flush()
    return len(expired)


def _release_stock(db: Session, order: models.ShopOrder) -> None:
    if not order.stock_locked:
        return
    for item in order.items:
        if item.product_id is None:
            continue
        product = db.get(models.Product, item.product_id)
        if product is None:
            continue
        product.stock_qty = int(product.stock_qty) + int(item.quantity)


def _lock_stock(db: Session, product: models.Product, qty: int) -> None:
    if product.stock_qty < qty:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock for {product.name} (have {product.stock_qty})",
        )
    product.stock_qty = int(product.stock_qty) - qty


def validate_checkout(db: Session, account: models.Account) -> dict:
    expire_stale_orders(db, account.id)
    cart = get_or_create_cart(db, account=account, session_id=None)
    cart_data = serialize_cart(db, cart)

    logged_in = True
    palm_enrolled = _palm_enrolled(account)
    wallet = get_linked_wallet(db, account, auto_link=True)
    wallet_balance = float(wallet.balance_pkr) if wallet else 0.0
    cart_total = float(cart_data["total_pkr"])
    balance_sufficient = wallet is not None and wallet_balance >= cart_total and cart_total > 0
    shortfall = None if balance_sufficient else max(0.0, cart_total - wallet_balance)

    if cart_data["item_count"] < 1:
        action = "empty_cart"
    elif cart_data["warnings"]:
        action = "fix_cart_warnings"
    elif not palm_enrolled:
        action = "enroll_palm"
    elif wallet is None:
        action = "link_wallet"
    elif not balance_sufficient:
        action = "topup_wallet"
    else:
        action = "proceed_to_scan"

    return {
        "logged_in": logged_in,
        "palm_enrolled": palm_enrolled,
        "balance_sufficient": balance_sufficient,
        "wallet_balance": wallet_balance,
        "cart_total": cart_total,
        "shortfall": shortfall,
        "action_required": action,
        "item_count": cart_data["item_count"],
        "warnings": cart_data["warnings"],
    }


def initiate_checkout(db: Session, account: models.Account) -> models.ShopOrder:
    validation = validate_checkout(db, account)
    if validation["action_required"] != "proceed_to_scan":
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Checkout not ready",
                "action_required": validation["action_required"],
                "validation": validation,
            },
        )

    cart = get_or_create_cart(db, account=account, session_id=None)
    cart = db.execute(
        select(models.Cart)
        .where(models.Cart.id == cart.id)
        .options(selectinload(models.Cart.items).selectinload(models.CartItem.product))
    ).scalar_one()

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Cancel any other pending locks for this customer
    pending = list(
        db.execute(
            select(models.ShopOrder)
            .where(
                models.ShopOrder.customer_id == account.id,
                models.ShopOrder.status == "pending",
            )
            .options(selectinload(models.ShopOrder.items))
        ).scalars().all()
    )
    for old in pending:
        _release_stock(db, old)
        old.status = "cancelled"
        old.payment_status = "failed"
        old.stock_locked = False
        old.updated_at = _utcnow()

    order_items: list[models.ShopOrderItem] = []
    subtotal = 0.0
    platform_fee_lines = 0.0

    for c_item in cart.items:
        product = c_item.product or db.get(models.Product, c_item.product_id)
        if product is None or not product.is_active or not product.is_approved:
            raise HTTPException(status_code=400, detail=f"Product unavailable: {c_item.product_id}")
        shop = db.get(models.Shop, product.shop_id)
        if shop is None or not shop.is_approved:
            raise HTTPException(status_code=400, detail=f"Shop unavailable for product {product.name}")

        qty = int(c_item.quantity)
        unit = float(product.price_pkr)  # charge current price
        line = unit * qty
        rate = float(shop.commission_rate or 0.05)
        platform_take = round(line * rate, 2)
        shop_earnings = round(line - platform_take, 2)

        _lock_stock(db, product, qty)

        order_items.append(
            models.ShopOrderItem(
                product_id=product.id,
                shop_id=shop.id,
                product_name=product.name,
                quantity=qty,
                unit_price=unit,
                line_total=line,
                shop_earnings=shop_earnings,
                platform_take=platform_take,
                commission_rate=rate,
            )
        )
        subtotal += line
        platform_fee_lines += platform_take

    platform_fee = round(platform_fee_lines + PLATFORM_FEE_PKR, 2)
    total = round(subtotal + PLATFORM_FEE_PKR, 2)

    order = models.ShopOrder(
        order_number=_new_order_number(),
        customer_id=account.id,
        status="pending",
        subtotal_pkr=round(subtotal, 2),
        platform_fee_pkr=platform_fee,
        total_pkr=total,
        payment_method="palm_vein",
        payment_status="pending",
        stock_locked=True,
        expires_at=_utcnow() + timedelta(minutes=ORDER_LOCK_TTL_MINUTES),
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(order)
    db.flush()
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)
    db.flush()
    return order


def cancel_checkout(db: Session, account: models.Account, order_id: int) -> models.ShopOrder:
    order = db.get(models.ShopOrder, order_id)
    if order is None or order.customer_id != account.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"Order is {order.status}")
    order = db.execute(
        select(models.ShopOrder)
        .where(models.ShopOrder.id == order_id)
        .options(selectinload(models.ShopOrder.items))
    ).scalar_one()
    _release_stock(db, order)
    order.status = "cancelled"
    order.payment_status = "failed"
    order.stock_locked = False
    order.updated_at = _utcnow()
    db.flush()
    return order


def palm_pay_order(
    db: Session,
    account: models.Account,
    *,
    order_id: int,
    confidence: float,
    scan_event_id: str | None = None,
) -> dict:
    expire_stale_orders(db, account.id)

    order = db.execute(
        select(models.ShopOrder)
        .where(models.ShopOrder.id == order_id)
        .options(selectinload(models.ShopOrder.items))
    ).scalar_one_or_none()
    if order is None or order.customer_id != account.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "confirmed" and order.payment_status == "paid":
        return _order_success_payload(db, order, already_paid=True)

    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"Order is {order.status}")

    if order.expires_at < _utcnow():
        _release_stock(db, order)
        order.status = "expired"
        order.payment_status = "failed"
        order.stock_locked = False
        order.updated_at = _utcnow()
        db.flush()
        raise HTTPException(status_code=410, detail="Order expired — stock released, retry checkout")

    order.scan_attempts = int(order.scan_attempts) + 1
    order.palm_confidence = confidence
    order.updated_at = _utcnow()

    if confidence < SHOP_PALM_CONFIDENCE_MIN:
        if order.scan_attempts >= MAX_SCAN_ATTEMPTS:
            _release_stock(db, order)
            order.status = "cancelled"
            order.payment_status = "failed"
            order.stock_locked = False
            order.notes = "Cancelled after 3 failed palm scans"
            db.flush()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Payment failed after 3 attempts. Your cart is saved.",
                    "code": "max_scan_attempts",
                    "scan_attempts": order.scan_attempts,
                },
            )
        db.flush()
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Palm not recognized. Try again",
                "code": "low_confidence",
                "confidence": confidence,
                "required": SHOP_PALM_CONFIDENCE_MIN,
                "scan_attempts": order.scan_attempts,
                "attempts_remaining": MAX_SCAN_ATTEMPTS - order.scan_attempts,
            },
        )

    if not _palm_enrolled(account):
        raise HTTPException(status_code=400, detail="Palm not enrolled")

    pp = resolve_or_link_palmpay_by_email(db, account, commit=False)
    if pp is None:
        raise HTTPException(status_code=400, detail="VeinPay wallet not linked")
    payer_wallet = get_or_create_wallet(db, pp)
    if payer_wallet.is_frozen:
        raise HTTPException(status_code=403, detail="Wallet is frozen")

    amount = float(order.total_pkr)
    if float(payer_wallet.balance_pkr) < amount:
        shortfall = amount - float(payer_wallet.balance_pkr)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Insufficient balance",
                "code": "insufficient_balance",
                "wallet_balance": float(payer_wallet.balance_pkr),
                "shortfall": shortfall,
            },
        )

    platform_pp, platform_wallet = ensure_platform_wallet(db)

    # Ensure each shop has a payout wallet
    shop_credits: list[tuple[models.Shop, models.PalmPayWallet, float]] = []
    by_shop: dict[int, float] = {}
    for item in order.items:
        if item.shop_id is None:
            continue
        by_shop[item.shop_id] = by_shop.get(item.shop_id, 0.0) + float(item.shop_earnings)

    for shop_id, earnings in by_shop.items():
        shop = db.get(models.Shop, shop_id)
        if shop is None:
            raise HTTPException(status_code=500, detail=f"Shop {shop_id} missing")
        owner = db.get(models.Account, shop.owner_user_id)
        if owner is None:
            raise HTTPException(status_code=500, detail="Shop owner missing")
        from backend.shop.identity_link import ensure_palmpay_link_for_account

        _owner_pp, shop_wallet = ensure_palmpay_link_for_account(db, owner, commit=False)
        if shop.wallet_id != shop_wallet.id:
            shop.wallet_id = shop_wallet.id
        shop_credits.append((shop, shop_wallet, earnings))

    platform_take_total = sum(float(i.platform_take) for i in order.items)

    idem = f"SHOPORD-{order.order_number}"
    existing = db.execute(
        select(models.PalmPayTransaction).where(models.PalmPayTransaction.idempotency_key == idem)
    ).scalar_one_or_none()
    if existing:
        order.status = "confirmed"
        order.payment_status = "paid"
        order.transaction_id = existing.id
        order.stock_locked = False  # already permanently reduced
        order.updated_at = _utcnow()
        db.flush()
        return _order_success_payload(db, order, already_paid=True)

    desc = f"Shop Purchase · {order.order_number}"
    if scan_event_id:
        desc = f"{desc} ({scan_event_id})"

    tx = models.PalmPayTransaction(
        reference=_new_ref("TX"),
        tx_type="shop_purchase",
        from_account_id=pp.id,
        to_account_id=platform_pp.id,
        amount_pkr=amount,
        status="complete",
        description=desc[:256],
        idempotency_key=idem,
        completed_at=_utcnow(),
    )
    db.add(tx)
    db.flush()

    # Atomic wallet moves
    payer_wallet.balance_pkr = float(payer_wallet.balance_pkr) - amount
    _write_ledger(
        db,
        transaction=tx,
        wallet=payer_wallet,
        entry_type="debit",
        amount_pkr=amount,
        balance_after=float(payer_wallet.balance_pkr),
    )

    for shop, shop_wallet, earnings in shop_credits:
        if earnings <= 0:
            continue
        shop_wallet.balance_pkr = float(shop_wallet.balance_pkr) + earnings
        _write_ledger(
            db,
            transaction=tx,
            wallet=shop_wallet,
            entry_type="credit",
            amount_pkr=earnings,
            balance_after=float(shop_wallet.balance_pkr),
        )

    if platform_take_total > 0:
        platform_wallet.balance_pkr = float(platform_wallet.balance_pkr) + platform_take_total
        _write_ledger(
            db,
            transaction=tx,
            wallet=platform_wallet,
            entry_type="credit",
            amount_pkr=platform_take_total,
            balance_after=float(platform_wallet.balance_pkr),
        )

    order.status = "confirmed"
    order.payment_status = "paid"
    order.transaction_id = tx.id
    order.stock_locked = False  # stock already deducted permanently
    order.updated_at = _utcnow()

    # Clear customer cart
    cart = get_or_create_cart(db, account=account, session_id=None)
    clear_cart(db, cart)

    # In-app notification (FCM stub)
    db.add(
        models.PalmPayUserNotification(
            account_id=pp.id,
            kind="shop_purchase",
            title="Payment Successful",
            body=f"PKR {amount:,.0f} paid. Order #{order.order_number}",
            payload_json=(
                f'{{"type":"shop_purchase","order_id":{order.id},'
                f'"amount":"{amount:.2f}","order_number":"{order.order_number}",'
                f'"new_balance":"{float(payer_wallet.balance_pkr):.2f}",'
                f'"transaction_id":{tx.id}}}'
            ),
        )
    )
    db.flush()
    invalidate_wallet_cache(pp.id)

    logger.info(
        "Shop palm-pay OK order=%s amount=%.2f customer=%s tx=%s conf=%.3f",
        order.order_number,
        amount,
        account.id,
        tx.reference,
        confidence,
    )
    return _order_success_payload(db, order, already_paid=False, new_balance=float(payer_wallet.balance_pkr))


def _order_success_payload(
    db: Session,
    order: models.ShopOrder,
    *,
    already_paid: bool,
    new_balance: float | None = None,
) -> dict:
    items = [
        {
            "product_name": i.product_name,
            "quantity": i.quantity,
            "unit_price": i.unit_price,
            "line_total": i.line_total,
            "shop_id": i.shop_id,
        }
        for i in order.items
    ]
    return {
        "success": True,
        "already_paid": already_paid,
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_pkr": order.total_pkr,
        "subtotal_pkr": order.subtotal_pkr,
        "platform_fee_pkr": order.platform_fee_pkr,
        "palm_confidence": order.palm_confidence,
        "transaction_id": order.transaction_id,
        "new_balance_pkr": new_balance,
        "items": items,
        "message": "Order confirmed" if not already_paid else "Order already paid",
    }


def serialize_order(order: models.ShopOrder) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "subtotal_pkr": order.subtotal_pkr,
        "platform_fee_pkr": order.platform_fee_pkr,
        "total_pkr": order.total_pkr,
        "scan_attempts": order.scan_attempts,
        "expires_at": order.expires_at,
        "created_at": order.created_at,
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "shop_id": i.shop_id,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "line_total": i.line_total,
                "shop_earnings": i.shop_earnings,
                "platform_take": i.platform_take,
            }
            for i in order.items
        ],
    }
