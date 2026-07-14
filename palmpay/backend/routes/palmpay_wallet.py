"""PalmPay wallet — balance, top-up, P2P transfer."""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.auth.palmpay_pin import DEFAULT_DEV_SPENDING_PIN
from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.settings import (
    PALMPAY_DEV_OTP,
    PALMPAY_JAZZCASH_WEBHOOK_SECRET,
)
from backend.wallet.palmpay_wallet_service import (
    complete_topup_order,
    confirm_transfer,
    create_topup_order,
    create_transfer_draft,
    get_or_create_wallet,
    lookup_recipient,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/palmpay", tags=["palmpay-wallet"])


class WalletResponse(BaseModel):
    account_number: str
    balance_pkr: float
    is_frozen: bool
    per_txn_limit_pkr: float
    daily_transfer_limit_pkr: float
    palm_pay_enabled: bool
    spending_pin_set: bool
    dev_spending_pin_hint: Optional[str] = None


class TransactionItem(BaseModel):
    reference: str
    tx_type: str
    direction: str
    amount_pkr: float
    counterparty_name: str
    description: str
    created_at: str


class TopUpInitiateRequest(BaseModel):
    amount_pkr: float = Field(gt=0, le=500_000)


class TopUpInitiateResponse(BaseModel):
    order_reference: str
    amount_pkr: float
    checkout_url: str
    message: str


class TopUpWebhookPayload(BaseModel):
    order_reference: str
    status: str = "paid"
    external_ref: Optional[str] = None


class TransferLookupItem(BaseModel):
    account_id: int
    full_name: str
    phone_masked: str


class TransferInitiateRequest(BaseModel):
    recipient_phone: str = Field(min_length=10, max_length=20)
    amount_pkr: float = Field(gt=0)
    note: Optional[str] = Field(default=None, max_length=256)


class TransferPreviewResponse(BaseModel):
    transfer_reference: str
    amount_pkr: float
    fee_pkr: float
    total_debit_pkr: float
    recipient_name: str
    recipient_phone_masked: str
    note: Optional[str]
    expires_in_seconds: int
    message: str


class TransferConfirmRequest(BaseModel):
    transfer_reference: str = Field(min_length=8, max_length=32)
    spending_pin: str = Field(min_length=4, max_length=6)


class TransferConfirmResponse(BaseModel):
    success: bool
    transaction_reference: str
    new_balance_pkr: float
    message: str


class WalletLimitsUpdateRequest(BaseModel):
    per_txn_limit_pkr: float = Field(ge=100, le=500_000)


class WalletSettingsUpdateRequest(BaseModel):
    is_frozen: Optional[bool] = None
    palm_pay_enabled: Optional[bool] = None


def _mask_phone(phone: str) -> str:
    if len(phone) < 4:
        return phone
    return f"{phone[:4]}***{phone[-2:]}"


def _checkout_base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.get("/wallet", response_model=WalletResponse)
def get_wallet(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> WalletResponse:
    from backend.settings import PALMPAY_DAILY_TRANSFER_LIMIT_PKR
    from backend.utils.wallet_cache import get_cached_wallet, set_cached_wallet

    cached = get_cached_wallet(account.id)
    if cached is not None:
        return WalletResponse(**cached)

    wallet = get_or_create_wallet(db, account)
    db.commit()
    payload = WalletResponse(
        account_number=wallet.account_number,
        balance_pkr=float(wallet.balance_pkr),
        is_frozen=wallet.is_frozen,
        per_txn_limit_pkr=float(wallet.per_txn_limit_pkr),
        daily_transfer_limit_pkr=PALMPAY_DAILY_TRANSFER_LIMIT_PKR,
        palm_pay_enabled=wallet.palm_pay_enabled,
        spending_pin_set=wallet.spending_pin_hash is not None,
        dev_spending_pin_hint=DEFAULT_DEV_SPENDING_PIN if PALMPAY_DEV_OTP else None,
    )
    set_cached_wallet(account.id, payload.model_dump())
    return payload


@router.get("/wallet/transactions", response_model=list[TransactionItem])
def recent_transactions(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
    limit: int = Query(default=5, ge=1, le=50),
) -> list[TransactionItem]:
    rows = db.execute(
        select(models.PalmPayTransaction)
        .where(
            or_(
                models.PalmPayTransaction.from_account_id == account.id,
                models.PalmPayTransaction.to_account_id == account.id,
            )
        )
        .where(models.PalmPayTransaction.status == "complete")
        .order_by(models.PalmPayTransaction.id.desc())
        .limit(limit)
    ).scalars().all()

    items: list[TransactionItem] = []
    for tx in rows:
        if tx.from_account_id == account.id:
            direction = "out"
            other_id = tx.to_account_id
        else:
            direction = "in"
            other_id = tx.from_account_id

        counterparty = "PalmPay"
        if other_id:
            other = db.get(models.PalmPayAccount, other_id)
            if other:
                counterparty = other.full_name or _mask_phone(other.phone)

        items.append(
            TransactionItem(
                reference=tx.reference,
                tx_type=tx.tx_type,
                direction=direction,
                amount_pkr=float(tx.amount_pkr),
                counterparty_name=counterparty,
                description=tx.description or tx.tx_type,
                created_at=tx.created_at.isoformat() if tx.created_at else "",
            )
        )
    return items


@router.post("/topup/jazzcash/initiate", response_model=TopUpInitiateResponse)
def topup_jazzcash_initiate(
    body: TopUpInitiateRequest,
    request: Request,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> TopUpInitiateResponse:
    order = create_topup_order(db, account=account, amount_pkr=body.amount_pkr)
    checkout_url = f"{_checkout_base(request)}/api/palmpay/topup/jazzcash/checkout/{order.reference}"
    return TopUpInitiateResponse(
        order_reference=order.reference,
        amount_pkr=float(order.amount_pkr),
        checkout_url=checkout_url,
        message="Open checkout to complete JazzCash payment",
    )


@router.get("/topup/jazzcash/checkout/{order_reference}", response_class=HTMLResponse)
def topup_jazzcash_checkout(
    order_reference: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    order = db.execute(
        select(models.PalmPayTopUpOrder).where(
            models.PalmPayTopUpOrder.reference == order_reference.upper()
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    amount = f"{float(order.amount_pkr):,.0f}"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PalmPay JazzCash</title>
<style>
body{{font-family:system-ui;background:#fafbfc;color:#111827;margin:0;padding:24px}}
.card{{max-width:420px;margin:40px auto;background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:24px;box-shadow:0 8px 24px rgba(17,24,39,0.08)}}
h1{{font-size:20px;margin:0 0 8px;color:#0db896}}
p{{color:#6b7280;line-height:1.5}}
.amount{{font-size:32px;font-weight:700;margin:16px 0;color:#111827}}
button{{width:100%;padding:14px;border:none;border-radius:12px;background:#1ce8b5;color:#0f172a;font-size:16px;font-weight:600;cursor:pointer}}
</style></head><body>
<div class="card">
<h1>JazzCash · PalmPay</h1>
<p>Dev checkout — simulates JazzCash wallet payment.</p>
<div class="amount">PKR {amount}</div>
<p>Order: {order.reference}</p>
<form method="post" action="/api/palmpay/topup/jazzcash/dev-complete">
<input type="hidden" name="order_reference" value="{order.reference}" />
<button type="submit">Pay with JazzCash (dev)</button>
</form>
</div></body></html>"""
    return HTMLResponse(html)


@router.post("/topup/jazzcash/simulate")
def topup_jazzcash_simulate(
    body: TopUpInitiateRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> dict:
    """Dev-only: credit wallet without JazzCash (mobile app shortcut)."""
    if not PALMPAY_DEV_OTP:
        raise HTTPException(status_code=403, detail="Dev simulate disabled")

    order = create_topup_order(db, account=account, amount_pkr=body.amount_pkr)
    tx = complete_topup_order(db, order=order, external_ref="dev-simulate")
    wallet = get_or_create_wallet(db, account)
    db.commit()
    return {
        "success": True,
        "order_reference": order.reference,
        "transaction_reference": tx.reference,
        "new_balance_pkr": float(wallet.balance_pkr),
        "message": "Top-up successful",
    }


class TopUpSimulateExistingRequest(BaseModel):
    order_reference: str = Field(min_length=8, max_length=32)


@router.post("/topup/jazzcash/simulate-existing")
def topup_simulate_existing(
    body: TopUpSimulateExistingRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> dict:
    if not PALMPAY_DEV_OTP:
        raise HTTPException(status_code=403, detail="Dev simulate disabled")

    order = db.execute(
        select(models.PalmPayTopUpOrder).where(
            models.PalmPayTopUpOrder.reference == body.order_reference.strip().upper()
        )
    ).scalar_one_or_none()
    if order is None or order.account_id != account.id:
        raise HTTPException(status_code=404, detail="Order not found")

    tx = complete_topup_order(db, order=order, external_ref="dev-simulate")
    wallet = get_or_create_wallet(db, account)
    db.commit()
    return {
        "success": True,
        "transaction_reference": tx.reference,
        "new_balance_pkr": float(wallet.balance_pkr),
        "message": "Top-up successful",
    }


@router.post("/topup/jazzcash/dev-complete")
def topup_jazzcash_dev_complete(
    order_reference: str = Form(...),
    db: Session = Depends(get_db),
) -> dict:
    if not PALMPAY_DEV_OTP:
        raise HTTPException(status_code=403, detail="Dev top-up disabled")
    ref = order_reference.strip().upper()
    if not ref:
        raise HTTPException(status_code=400, detail="order_reference required")

    order = db.execute(
        select(models.PalmPayTopUpOrder).where(models.PalmPayTopUpOrder.reference == ref)
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    tx = complete_topup_order(db, order=order, external_ref="dev-jazzcash")
    wallet = db.get(models.PalmPayAccount, order.account_id)
    balance = float(wallet.wallet.balance_pkr) if wallet and wallet.wallet else 0.0
    return {
        "success": True,
        "transaction_reference": tx.reference,
        "new_balance_pkr": balance,
        "message": "Top-up successful",
    }


@router.post("/topup/jazzcash/webhook")
def topup_jazzcash_webhook(
    body: TopUpWebhookPayload,
    db: Session = Depends(get_db),
    x_palmpay_signature: Optional[str] = Header(default=None),
) -> dict:
    payload = body.model_dump_json()
    expected = hmac.new(
        PALMPAY_JAZZCASH_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    if x_palmpay_signature and not hmac.compare_digest(x_palmpay_signature, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if body.status != "paid":
        return {"success": False, "message": "Ignored non-paid status"}

    order = db.execute(
        select(models.PalmPayTopUpOrder).where(
            models.PalmPayTopUpOrder.reference == body.order_reference.strip().upper()
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    tx = complete_topup_order(db, order=order, external_ref=body.external_ref)
    return {"success": True, "transaction_reference": tx.reference}


@router.get("/transfer/lookup", response_model=list[TransferLookupItem])
def transfer_lookup(
    q: str = Query(min_length=3, max_length=32),
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> list[TransferLookupItem]:
    phone = q.strip()
    results: list[TransferLookupItem] = []

    normalized = lookup_recipient(db, phone)
    if normalized and normalized.id != account.id:
        results.append(
            TransferLookupItem(
                account_id=normalized.id,
                full_name=normalized.full_name,
                phone_masked=_mask_phone(normalized.phone),
            )
        )
        return results

    rows = db.execute(
        select(models.PalmPayAccount)
        .where(models.PalmPayAccount.id != account.id)
        .where(
            or_(
                models.PalmPayAccount.phone.contains(phone),
                models.PalmPayAccount.full_name.ilike(f"%{phone}%"),
            )
        )
        .limit(8)
    ).scalars().all()

    for row in rows:
        results.append(
            TransferLookupItem(
                account_id=row.id,
                full_name=row.full_name,
                phone_masked=_mask_phone(row.phone),
            )
        )
    return results


@router.post("/transfer/initiate", response_model=TransferPreviewResponse)
def transfer_initiate(
    body: TransferInitiateRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> TransferPreviewResponse:
    from backend.settings import PALMPAY_TRANSFER_DRAFT_TTL_S

    draft, recipient = create_transfer_draft(
        db,
        sender=account,
        recipient_phone=body.recipient_phone,
        amount_pkr=body.amount_pkr,
        note=body.note,
    )
    return TransferPreviewResponse(
        transfer_reference=draft.reference,
        amount_pkr=float(draft.amount_pkr),
        fee_pkr=0.0,
        total_debit_pkr=float(draft.amount_pkr),
        recipient_name=recipient.full_name or "PalmPay user",
        recipient_phone_masked=_mask_phone(recipient.phone),
        note=draft.note,
        expires_in_seconds=PALMPAY_TRANSFER_DRAFT_TTL_S,
        message="Confirm with your spending PIN to send",
    )


@router.post("/transfer/confirm", response_model=TransferConfirmResponse)
def transfer_confirm(
    body: TransferConfirmRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> TransferConfirmResponse:
    tx = confirm_transfer(
        db,
        sender=account,
        transfer_reference=body.transfer_reference,
        spending_pin=body.spending_pin,
    )
    wallet = get_or_create_wallet(db, account)
    db.commit()
    return TransferConfirmResponse(
        success=True,
        transaction_reference=tx.reference,
        new_balance_pkr=float(wallet.balance_pkr),
        message="Transfer sent successfully",
    )


@router.put("/wallet/limits", response_model=WalletResponse)
def update_wallet_limits(
    body: WalletLimitsUpdateRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> WalletResponse:
    from backend.settings import PALMPAY_DAILY_TRANSFER_LIMIT_PKR

    wallet = get_or_create_wallet(db, account)
    wallet.per_txn_limit_pkr = float(body.per_txn_limit_pkr)
    db.commit()
    db.refresh(wallet)
    invalidate_wallet_cache(account.id)

    return WalletResponse(
        account_number=wallet.account_number,
        balance_pkr=float(wallet.balance_pkr),
        is_frozen=wallet.is_frozen,
        per_txn_limit_pkr=float(wallet.per_txn_limit_pkr),
        daily_transfer_limit_pkr=PALMPAY_DAILY_TRANSFER_LIMIT_PKR,
        palm_pay_enabled=wallet.palm_pay_enabled,
        spending_pin_set=wallet.spending_pin_hash is not None,
        dev_spending_pin_hint=DEFAULT_DEV_SPENDING_PIN if PALMPAY_DEV_OTP else None,
    )


@router.put("/wallet/settings", response_model=WalletResponse)
def update_wallet_settings(
    body: WalletSettingsUpdateRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> WalletResponse:
    from backend.settings import PALMPAY_DAILY_TRANSFER_LIMIT_PKR

    wallet = get_or_create_wallet(db, account)
    if body.is_frozen is not None:
        wallet.is_frozen = bool(body.is_frozen)
    if body.palm_pay_enabled is not None:
        wallet.palm_pay_enabled = bool(body.palm_pay_enabled)

    db.commit()
    db.refresh(wallet)
    invalidate_wallet_cache(account.id)
    return WalletResponse(
        account_number=wallet.account_number,
        balance_pkr=float(wallet.balance_pkr),
        is_frozen=wallet.is_frozen,
        per_txn_limit_pkr=float(wallet.per_txn_limit_pkr),
        daily_transfer_limit_pkr=PALMPAY_DAILY_TRANSFER_LIMIT_PKR,
        palm_pay_enabled=wallet.palm_pay_enabled,
        spending_pin_set=wallet.spending_pin_hash is not None,
        dev_spending_pin_hint=DEFAULT_DEV_SPENDING_PIN if PALMPAY_DEV_OTP else None,
    )
