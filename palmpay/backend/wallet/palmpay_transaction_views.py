"""Map PalmPay transaction rows to API view models."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.db import models


def _mask_phone(phone: str) -> str:
    if len(phone) < 4:
        return phone
    return f"{phone[:4]}***{phone[-2:]}"


def counterparty_name(db: Session, account_id: int, tx: models.PalmPayTransaction) -> str:
    if tx.from_account_id == account_id:
        other_id = tx.to_account_id
    else:
        other_id = tx.from_account_id

    if other_id is None:
        if tx.tx_type == "topup":
            return "Wallet top-up"
        if tx.tx_type == "palm_pay":
            return "Merchant payment"
        return "PalmPay"

    other = db.get(models.PalmPayAccount, other_id)
    if other is None:
        return "PalmPay"
    return other.full_name or _mask_phone(other.phone)


def transaction_direction(account_id: int, tx: models.PalmPayTransaction) -> str:
    return "out" if tx.from_account_id == account_id else "in"


def transaction_to_dict(db: Session, account_id: int, tx: models.PalmPayTransaction) -> dict:
    return {
        "reference": tx.reference,
        "tx_type": tx.tx_type,
        "direction": transaction_direction(account_id, tx),
        "amount_pkr": float(tx.amount_pkr),
        "counterparty_name": counterparty_name(db, account_id, tx),
        "description": tx.description or tx.tx_type.replace("_", " ").title(),
        "created_at": tx.created_at.isoformat() if tx.created_at else "",
        "status": tx.status,
        "topup_method": tx.topup_method,
        "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
    }


def account_transactions_base(account_id: int):
    return (
        select(models.PalmPayTransaction)
        .where(
            or_(
                models.PalmPayTransaction.from_account_id == account_id,
                models.PalmPayTransaction.to_account_id == account_id,
            )
        )
        .where(models.PalmPayTransaction.status == "complete")
    )


def parse_period_start(period: str) -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if period == "month":
        return now - timedelta(days=30)
    return now - timedelta(days=7)


def analytics_summary(db: Session, account_id: int, period: str) -> dict:
    since = parse_period_start(period)
    rows = db.execute(
        account_transactions_base(account_id)
        .where(models.PalmPayTransaction.created_at >= since)
        .order_by(models.PalmPayTransaction.created_at.asc())
    ).scalars().all()

    total_in = 0.0
    total_out = 0.0
    by_type: dict[str, dict] = {}
    daily: dict[str, dict] = {}

    for tx in rows:
        direction = transaction_direction(account_id, tx)
        amount = float(tx.amount_pkr)
        if direction == "in":
            total_in += amount
        else:
            total_out += amount

        bucket = by_type.setdefault(
            tx.tx_type,
            {"tx_type": tx.tx_type, "count": 0, "amount_pkr": 0.0},
        )
        bucket["count"] += 1
        bucket["amount_pkr"] += amount

        day_key = tx.created_at.strftime("%Y-%m-%d") if tx.created_at else "unknown"
        day = daily.setdefault(day_key, {"date": day_key, "in_pkr": 0.0, "out_pkr": 0.0})
        if direction == "in":
            day["in_pkr"] += amount
        else:
            day["out_pkr"] += amount

    return {
        "period": period,
        "total_in_pkr": round(total_in, 2),
        "total_out_pkr": round(total_out, 2),
        "net_pkr": round(total_in - total_out, 2),
        "tx_count": len(rows),
        "by_type": sorted(by_type.values(), key=lambda x: x["amount_pkr"], reverse=True),
        "daily": [daily[k] for k in sorted(daily.keys())],
    }
