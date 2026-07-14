"""PalmPay wallet ledger, top-up, and P2P transfer logic."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.auth.palmpay_phone import normalize_pk_phone
from backend.auth.palmpay_pin import hash_spending_pin, verify_spending_pin
from backend.db import models
from backend.settings import (
    PALMPAY_DAILY_TRANSFER_LIMIT_PKR,
    PALMPAY_DEV_SPENDING_PIN,
    PALMPAY_TRANSFER_DRAFT_TTL_S,
)

from backend.utils.wallet_cache import invalidate_wallet_cache

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _new_ref(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(6).upper()}"


def ensure_wallet_settings(wallet: models.PalmPayWallet) -> None:
    if wallet.spending_pin_hash is None:
        wallet.spending_pin_hash = hash_spending_pin(PALMPAY_DEV_SPENDING_PIN)


def get_or_create_wallet(db: Session, account: models.PalmPayAccount) -> models.PalmPayWallet:
    wallet = account.wallet
    if wallet is None:
        wallet = models.PalmPayWallet(
            account_id=account.id,
            balance_pkr=0.0,
            account_number=f"PP{secrets.token_hex(4).upper()}",
        )
        db.add(wallet)
        db.flush()
    ensure_wallet_settings(wallet)
    return wallet


def _daily_sent_total(db: Session, account_id: int) -> float:
    start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total = db.execute(
        select(func.coalesce(func.sum(models.PalmPayTransaction.amount_pkr), 0.0))
        .where(models.PalmPayTransaction.from_account_id == account_id)
        .where(models.PalmPayTransaction.tx_type == "transfer")
        .where(models.PalmPayTransaction.status == "complete")
        .where(models.PalmPayTransaction.created_at >= start)
    ).scalar_one()
    return float(total or 0.0)


def _write_ledger(
    db: Session,
    *,
    transaction: models.PalmPayTransaction,
    wallet: models.PalmPayWallet,
    entry_type: str,
    amount_pkr: float,
    balance_after: float,
) -> None:
    db.add(
        models.PalmPayLedgerEntry(
            transaction_id=transaction.id,
            wallet_id=wallet.id,
            entry_type=entry_type,
            amount_pkr=amount_pkr,
            balance_after=balance_after,
        )
    )


def credit_wallet(
    db: Session,
    *,
    account: models.PalmPayAccount,
    amount_pkr: float,
    tx_type: str,
    description: str,
    topup_method: str | None = None,
    topup_ref: str | None = None,
) -> models.PalmPayTransaction:
    if amount_pkr <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    wallet = get_or_create_wallet(db, account)
    if wallet.is_frozen:
        raise HTTPException(status_code=403, detail="Wallet is frozen")

    tx = models.PalmPayTransaction(
        reference=_new_ref("TX"),
        tx_type=tx_type,
        to_account_id=account.id,
        amount_pkr=amount_pkr,
        status="complete",
        description=description,
        topup_method=topup_method,
        topup_ref=topup_ref,
        completed_at=_utcnow(),
    )
    db.add(tx)
    db.flush()

    wallet.balance_pkr = float(wallet.balance_pkr) + amount_pkr
    _write_ledger(
        db,
        transaction=tx,
        wallet=wallet,
        entry_type="credit",
        amount_pkr=amount_pkr,
        balance_after=float(wallet.balance_pkr),
    )
    return tx


def lookup_recipient(db: Session, query: str) -> models.PalmPayAccount | None:
    phone = normalize_pk_phone(query)
    if phone:
        return db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()

    q = query.strip()
    if not q:
        return None

    return db.execute(
        select(models.PalmPayAccount)
        .where(
            or_(
                models.PalmPayAccount.full_name.ilike(f"%{q}%"),
                models.PalmPayAccount.phone.contains(q),
            )
        )
        .limit(1)
    ).scalar_one_or_none()


def create_transfer_draft(
    db: Session,
    *,
    sender: models.PalmPayAccount,
    recipient_phone: str,
    amount_pkr: float,
    note: str | None,
) -> tuple[models.PalmPayTransferDraft, models.PalmPayAccount]:
    if amount_pkr <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    phone = normalize_pk_phone(recipient_phone)
    if phone is None:
        raise HTTPException(status_code=400, detail="Invalid recipient phone number")

    recipient = db.execute(
        select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
    ).scalar_one_or_none()
    if recipient is None:
        raise HTTPException(status_code=404, detail="User not found")
    if recipient.id == sender.id:
        raise HTTPException(status_code=400, detail="Cannot send money to yourself")

    sender_wallet = get_or_create_wallet(db, sender)
    if sender_wallet.is_frozen:
        raise HTTPException(status_code=403, detail="Wallet is frozen")
    if amount_pkr > float(sender_wallet.per_txn_limit_pkr):
        raise HTTPException(
            status_code=400,
            detail=f"Amount exceeds per-transaction limit of PKR {sender_wallet.per_txn_limit_pkr:,.0f}",
        )

    daily_sent = _daily_sent_total(db, sender.id)
    if daily_sent + amount_pkr > PALMPAY_DAILY_TRANSFER_LIMIT_PKR:
        raise HTTPException(
            status_code=400,
            detail=f"Daily transfer limit of PKR {PALMPAY_DAILY_TRANSFER_LIMIT_PKR:,.0f} exceeded",
        )

    if float(sender_wallet.balance_pkr) < amount_pkr:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    draft = models.PalmPayTransferDraft(
        reference=_new_ref("TR"),
        sender_account_id=sender.id,
        recipient_account_id=recipient.id,
        amount_pkr=amount_pkr,
        note=(note or "").strip() or None,
        status="pending",
        expires_at=_utcnow() + timedelta(seconds=PALMPAY_TRANSFER_DRAFT_TTL_S),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft, recipient


def confirm_transfer(
    db: Session,
    *,
    sender: models.PalmPayAccount,
    transfer_reference: str,
    spending_pin: str,
) -> models.PalmPayTransaction:
    draft = db.execute(
        select(models.PalmPayTransferDraft).where(
            models.PalmPayTransferDraft.reference == transfer_reference.strip().upper()
        )
    ).scalar_one_or_none()
    if draft is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if draft.sender_account_id != sender.id:
        raise HTTPException(status_code=403, detail="Not your transfer")
    if draft.status != "pending":
        raise HTTPException(status_code=400, detail=f"Transfer is {draft.status}")
    if draft.expires_at < _utcnow():
        draft.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Transfer preview expired — start again")

    sender_wallet = get_or_create_wallet(db, sender)
    if not verify_spending_pin(spending_pin, sender_wallet.spending_pin_hash):
        raise HTTPException(status_code=401, detail="Incorrect spending PIN")

    recipient = db.get(models.PalmPayAccount, draft.recipient_account_id)
    if recipient is None:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient_wallet = get_or_create_wallet(db, recipient)
    amount = float(draft.amount_pkr)

    db.refresh(sender_wallet)
    if float(sender_wallet.balance_pkr) < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    tx = models.PalmPayTransaction(
        reference=_new_ref("TX"),
        tx_type="transfer",
        from_account_id=sender.id,
        to_account_id=recipient.id,
        amount_pkr=amount,
        status="complete",
        description=draft.note or f"Transfer to {recipient.full_name or recipient.phone}",
        completed_at=_utcnow(),
    )
    db.add(tx)
    db.flush()

    sender_wallet.balance_pkr = float(sender_wallet.balance_pkr) - amount
    recipient_wallet.balance_pkr = float(recipient_wallet.balance_pkr) + amount

    _write_ledger(
        db,
        transaction=tx,
        wallet=sender_wallet,
        entry_type="debit",
        amount_pkr=amount,
        balance_after=float(sender_wallet.balance_pkr),
    )
    _write_ledger(
        db,
        transaction=tx,
        wallet=recipient_wallet,
        entry_type="credit",
        amount_pkr=amount,
        balance_after=float(recipient_wallet.balance_pkr),
    )

    draft.status = "confirmed"
    db.commit()
    db.refresh(tx)
    invalidate_wallet_cache(sender.id)
    invalidate_wallet_cache(recipient.id)
    logger.info(
        "P2P transfer %s PKR from account %s to %s (tx=%s)",
        amount,
        sender.id,
        recipient.id,
        tx.reference,
    )
    return tx


def create_topup_order(
    db: Session,
    *,
    account: models.PalmPayAccount,
    amount_pkr: float,
) -> models.PalmPayTopUpOrder:
    if amount_pkr < 100:
        raise HTTPException(status_code=400, detail="Minimum top-up is PKR 100")
    if amount_pkr > 500_000:
        raise HTTPException(status_code=400, detail="Maximum top-up is PKR 500,000")

    wallet = get_or_create_wallet(db, account)
    if wallet.is_frozen:
        raise HTTPException(status_code=403, detail="Wallet is frozen")

    order = models.PalmPayTopUpOrder(
        reference=_new_ref("TU"),
        account_id=account.id,
        amount_pkr=amount_pkr,
        method="jazzcash",
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def complete_topup_order(
    db: Session,
    *,
    order: models.PalmPayTopUpOrder,
    external_ref: str | None = None,
) -> models.PalmPayTransaction:
    if order.status == "paid":
        existing = db.execute(
            select(models.PalmPayTransaction)
            .where(models.PalmPayTransaction.topup_ref == order.reference)
            .limit(1)
        ).scalar_one_or_none()
        if existing:
            return existing
        raise HTTPException(status_code=400, detail="Top-up already processed")

    account = db.get(models.PalmPayAccount, order.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    order.status = "paid"
    order.paid_at = _utcnow()
    order.external_ref = external_ref

    tx = credit_wallet(
        db,
        account=account,
        amount_pkr=float(order.amount_pkr),
        tx_type="topup",
        description=f"JazzCash top-up PKR {order.amount_pkr:,.0f}",
        topup_method=order.method,
        topup_ref=order.reference,
    )
    db.commit()
    db.refresh(tx)
    invalidate_wallet_cache(account.id)
    return tx
