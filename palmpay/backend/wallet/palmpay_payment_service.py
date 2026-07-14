"""Palm Pay — payment requests, orchestration, merchant seed."""
from __future__ import annotations

import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.db import models
from backend.settings import (
    PALMPAY_DAILY_TRANSFER_LIMIT_PKR,
    PALMPAY_PALM_MATCH_THRESHOLD,
    PALMPAY_PAYMENT_REQUEST_TTL_S,
)
from backend.wallet.palmpay_wallet_service import _write_ledger, get_or_create_wallet
from backend.utils.wallet_cache import invalidate_wallet_cache

logger = logging.getLogger(__name__)

DEV_MERCHANT_CODE = "DEMO01"
DEV_MERCHANT_PHONE = "03999999999"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _new_ref(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(6).upper()}"


@dataclass
class PalmPaymentResult:
    success: bool
    request_reference: str
    status: str
    merchant_name: str
    amount_pkr: float
    failure_code: str | None = None
    failure_reason: str | None = None
    transaction_reference: str | None = None
    new_balance_pkr: float | None = None
    shortfall_pkr: float | None = None
    confidence: float | None = None

    def to_ws_payload(self) -> dict:
        return {
            "status": self.status,
            "success": self.success,
            "request_reference": self.request_reference,
            "merchant_name": self.merchant_name,
            "amount_pkr": self.amount_pkr,
            "failure_code": self.failure_code,
            "failure_reason": self.failure_reason,
            "transaction_reference": self.transaction_reference,
            "new_balance_pkr": self.new_balance_pkr,
            "shortfall_pkr": self.shortfall_pkr,
            "confidence": self.confidence,
        }

    def to_notification_payload(self) -> dict:
        return {
            "request_reference": self.request_reference,
            "merchant_name": self.merchant_name,
            "amount_pkr": self.amount_pkr,
            "transaction_reference": self.transaction_reference,
            "failure_code": self.failure_code,
            "shortfall_pkr": self.shortfall_pkr,
        }


def ensure_dev_merchant(db: Session) -> models.PalmPayMerchant:
    existing = db.execute(
        select(models.PalmPayMerchant).where(models.PalmPayMerchant.code == DEV_MERCHANT_CODE)
    ).scalar_one_or_none()
    if existing:
        return existing

    account = db.execute(
        select(models.PalmPayAccount).where(models.PalmPayAccount.phone == DEV_MERCHANT_PHONE)
    ).scalar_one_or_none()
    if account is None:
        account = models.PalmPayAccount(
            phone=DEV_MERCHANT_PHONE,
            full_name="Demo Coffee Shop",
            kyc_status="verified",
        )
        db.add(account)
        db.flush()
        get_or_create_wallet(db, account)

    merchant = models.PalmPayMerchant(
        code=DEV_MERCHANT_CODE,
        name="Demo Coffee Shop",
        category="cafe",
        account_id=account.id,
        is_active=True,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    logger.info("Seeded dev merchant %s (%s)", merchant.name, merchant.code)
    return merchant


def list_active_merchants(db: Session) -> list[models.PalmPayMerchant]:
    ensure_dev_merchant(db)
    return list(
        db.execute(
            select(models.PalmPayMerchant)
            .where(models.PalmPayMerchant.is_active.is_(True))
            .order_by(models.PalmPayMerchant.name)
        ).scalars().all()
    )


def get_merchant_by_code(db: Session, code: str) -> models.PalmPayMerchant:
    merchant = db.execute(
        select(models.PalmPayMerchant).where(models.PalmPayMerchant.code == code.strip().upper())
    ).scalar_one_or_none()
    if merchant is None or not merchant.is_active:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return merchant


def create_payment_request(
    db: Session,
    *,
    merchant: models.PalmPayMerchant,
    amount_pkr: float,
    kiosk_id: str,
) -> models.PalmPayPaymentRequest:
    if amount_pkr <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
    if amount_pkr > 500_000:
        raise HTTPException(status_code=400, detail="Amount exceeds kiosk limit")

    req = models.PalmPayPaymentRequest(
        reference=_new_ref("PR"),
        merchant_id=merchant.id,
        kiosk_id=kiosk_id or "kiosk-dev",
        amount_pkr=amount_pkr,
        status="pending",
        expires_at=_utcnow() + timedelta(seconds=PALMPAY_PAYMENT_REQUEST_TTL_S),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def _daily_debit_total(db: Session, account_id: int) -> float:
    start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total = db.execute(
        select(func.coalesce(func.sum(models.PalmPayTransaction.amount_pkr), 0.0))
        .where(models.PalmPayTransaction.from_account_id == account_id)
        .where(models.PalmPayTransaction.tx_type.in_(("transfer", "palm_pay")))
        .where(models.PalmPayTransaction.status == "complete")
        .where(models.PalmPayTransaction.created_at >= start)
    ).scalar_one()
    return float(total or 0.0)


def _load_request(db: Session, reference: str) -> models.PalmPayPaymentRequest:
    req = db.execute(
        select(models.PalmPayPaymentRequest).where(
            models.PalmPayPaymentRequest.reference == reference.strip().upper()
        )
    ).scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=404, detail="Payment request not found")
    return req


def _result_from_existing(db: Session, req: models.PalmPayPaymentRequest) -> PalmPaymentResult:
    merchant_name = req.merchant.name if req.merchant else "Merchant"
    tx_ref = None
    new_balance = None
    if req.transaction_id:
        tx = db.get(models.PalmPayTransaction, req.transaction_id)
        if tx:
            tx_ref = tx.reference
    if req.payer_account_id and req.status == "completed":
        wallet = get_or_create_wallet(db, db.get(models.PalmPayAccount, req.payer_account_id))
        new_balance = float(wallet.balance_pkr)

    return PalmPaymentResult(
        success=req.status == "completed",
        request_reference=req.reference,
        status=req.status,
        merchant_name=merchant_name,
        amount_pkr=float(req.amount_pkr),
        failure_code=req.failure_code,
        failure_reason=req.failure_reason,
        transaction_reference=tx_ref,
        new_balance_pkr=new_balance,
        shortfall_pkr=None,
        confidence=req.match_confidence,
    )


def _fail_request(
    db: Session,
    req: models.PalmPayPaymentRequest,
    *,
    code: str,
    reason: str,
    payer_account_id: int | None = None,
    confidence: float | None = None,
    shortfall: float | None = None,
) -> PalmPaymentResult:
    req.status = "failed"
    req.failure_code = code
    req.failure_reason = reason
    req.payer_account_id = payer_account_id
    req.match_confidence = confidence
    req.completed_at = _utcnow()
    db.commit()
    db.refresh(req)

    result = PalmPaymentResult(
        success=False,
        request_reference=req.reference,
        status="failed",
        merchant_name=req.merchant.name if req.merchant else "Merchant",
        amount_pkr=float(req.amount_pkr),
        failure_code=code,
        failure_reason=reason,
        shortfall_pkr=shortfall,
        confidence=confidence,
    )
    if payer_account_id:
        _create_notification(db, payer_account_id, result)
    db.commit()
    return result


def _create_notification(db: Session, account_id: int, result: PalmPaymentResult) -> None:
    if result.success:
        kind = "palm_pay_success"
        title = "Payment successful"
        body = f"Rs. {result.amount_pkr:,.0f} paid to {result.merchant_name}"
    elif result.failure_code == "insufficient_balance":
        kind = "palm_pay_low_balance"
        title = "Payment failed — low balance"
        body = f"Add Rs. {(result.shortfall_pkr or 0):,.0f} to pay {result.merchant_name}"
    else:
        kind = "palm_pay_failed"
        title = "Payment failed"
        body = result.failure_reason or "Could not complete palm payment"

    db.add(
        models.PalmPayUserNotification(
            account_id=account_id,
            kind=kind,
            title=title,
            body=body,
            payload_json=json.dumps(result.to_notification_payload()),
        )
    )


def process_palm_payment(
    db: Session,
    *,
    request_reference: str,
    payer_account_id: int,
    confidence: float,
    scan_event_id: str | None = None,
) -> PalmPaymentResult:
    req = _load_request(db, request_reference)

    if req.status in ("completed", "failed"):
        return _result_from_existing(db, req)

    if req.expires_at < _utcnow() and req.status == "pending":
        req.status = "expired"
        req.failure_code = "request_expired"
        req.failure_reason = "Payment request expired — ask merchant to try again"
        req.completed_at = _utcnow()
        db.commit()
        return PalmPaymentResult(
            success=False,
            request_reference=req.reference,
            status="expired",
            merchant_name=req.merchant.name if req.merchant else "Merchant",
            amount_pkr=float(req.amount_pkr),
            failure_code="request_expired",
            failure_reason=req.failure_reason,
        )

    merchant_name = req.merchant.name if req.merchant else "Merchant"
    amount = float(req.amount_pkr)

    if confidence < PALMPAY_PALM_MATCH_THRESHOLD:
        return _fail_request(
            db,
            req,
            code="low_confidence",
            reason="Palm not recognized — please try again",
            payer_account_id=payer_account_id,
            confidence=confidence,
        )

    payer = db.get(models.PalmPayAccount, payer_account_id)
    if payer is None:
        return _fail_request(
            db,
            req,
            code="user_not_found",
            reason="Account not found",
            confidence=confidence,
        )

    payer_wallet = get_or_create_wallet(db, payer)
    if payer_wallet.is_frozen:
        return _fail_request(
            db,
            req,
            code="wallet_frozen",
            reason="Your wallet is frozen",
            payer_account_id=payer.id,
            confidence=confidence,
        )
    if not payer_wallet.palm_pay_enabled:
        return _fail_request(
            db,
            req,
            code="palm_pay_disabled",
            reason="Palm Pay is disabled on your wallet",
            payer_account_id=payer.id,
            confidence=confidence,
        )
    if amount > float(payer_wallet.per_txn_limit_pkr):
        return _fail_request(
            db,
            req,
            code="limit_exceeded",
            reason=f"Amount exceeds your per-transaction limit of PKR {payer_wallet.per_txn_limit_pkr:,.0f}",
            payer_account_id=payer.id,
            confidence=confidence,
        )

    daily_debit = _daily_debit_total(db, payer.id)
    if daily_debit + amount > PALMPAY_DAILY_TRANSFER_LIMIT_PKR:
        return _fail_request(
            db,
            req,
            code="limit_exceeded",
            reason=f"Daily spending limit of PKR {PALMPAY_DAILY_TRANSFER_LIMIT_PKR:,.0f} exceeded",
            payer_account_id=payer.id,
            confidence=confidence,
        )

    balance = float(payer_wallet.balance_pkr)
    if balance < amount:
        shortfall = amount - balance
        return _fail_request(
            db,
            req,
            code="insufficient_balance",
            reason=f"Insufficient balance — need Rs. {shortfall:,.0f} more",
            payer_account_id=payer.id,
            confidence=confidence,
            shortfall=shortfall,
        )

    merchant = req.merchant
    if merchant is None or merchant.account_id is None:
        return _fail_request(
            db,
            req,
            code="merchant_error",
            reason="Merchant cannot receive payments",
            payer_account_id=payer.id,
            confidence=confidence,
        )

    merchant_account = db.get(models.PalmPayAccount, merchant.account_id)
    if merchant_account is None:
        return _fail_request(
            db,
            req,
            code="merchant_error",
            reason="Merchant account missing",
            payer_account_id=payer.id,
            confidence=confidence,
        )

    merchant_wallet = get_or_create_wallet(db, merchant_account)

    existing_tx = db.execute(
        select(models.PalmPayTransaction).where(
            models.PalmPayTransaction.idempotency_key == req.reference
        )
    ).scalar_one_or_none()
    if existing_tx:
        req.status = "completed"
        req.payer_account_id = payer.id
        req.transaction_id = existing_tx.id
        req.match_confidence = confidence
        req.completed_at = _utcnow()
        db.commit()
        return _result_from_existing(db, req)

    description = f"Palm Pay · {merchant_name}"
    if scan_event_id:
        description = f"{description} ({scan_event_id})"

    tx = models.PalmPayTransaction(
        reference=_new_ref("TX"),
        tx_type="palm_pay",
        from_account_id=payer.id,
        to_account_id=merchant_account.id,
        amount_pkr=amount,
        status="complete",
        description=description,
        merchant_id=merchant.id,
        payment_request_id=req.id,
        idempotency_key=req.reference,
        completed_at=_utcnow(),
    )
    db.add(tx)
    db.flush()

    payer_wallet.balance_pkr = balance - amount
    merchant_wallet.balance_pkr = float(merchant_wallet.balance_pkr) + amount

    _write_ledger(
        db,
        transaction=tx,
        wallet=payer_wallet,
        entry_type="debit",
        amount_pkr=amount,
        balance_after=float(payer_wallet.balance_pkr),
    )
    _write_ledger(
        db,
        transaction=tx,
        wallet=merchant_wallet,
        entry_type="credit",
        amount_pkr=amount,
        balance_after=float(merchant_wallet.balance_pkr),
    )

    req.status = "completed"
    req.payer_account_id = payer.id
    req.transaction_id = tx.id
    req.match_confidence = confidence
    req.completed_at = _utcnow()
    db.flush()

    result = PalmPaymentResult(
        success=True,
        request_reference=req.reference,
        status="completed",
        merchant_name=merchant_name,
        amount_pkr=amount,
        transaction_reference=tx.reference,
        new_balance_pkr=float(payer_wallet.balance_pkr),
        confidence=confidence,
    )
    _create_notification(db, payer.id, result)
    db.commit()
    invalidate_wallet_cache(payer.id)

    logger.info(
        "Palm Pay %s PKR from account %s to merchant %s (tx=%s, conf=%.3f)",
        amount,
        payer.id,
        merchant.code,
        tx.reference,
        confidence,
    )
    return result


def get_unread_notifications(db: Session, account_id: int, limit: int = 10) -> list[models.PalmPayUserNotification]:
    return list(
        db.execute(
            select(models.PalmPayUserNotification)
            .where(models.PalmPayUserNotification.account_id == account_id)
            .where(models.PalmPayUserNotification.read_at.is_(None))
            .order_by(models.PalmPayUserNotification.id.desc())
            .limit(limit)
        ).scalars().all()
    )


def mark_notification_read(db: Session, account_id: int, notification_id: int) -> None:
    note = db.get(models.PalmPayUserNotification, notification_id)
    if note is None or note.account_id != account_id:
        raise HTTPException(status_code=404, detail="Notification not found")
    if note.read_at is None:
        note.read_at = _utcnow()
        db.commit()
