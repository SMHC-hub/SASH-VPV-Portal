"""PalmPay transaction history and spending analytics."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.wallet.palmpay_transaction_views import (
    account_transactions_base,
    analytics_summary,
    transaction_to_dict,
)

router = APIRouter(prefix="/api/palmpay", tags=["palmpay-transactions"])


class TransactionItem(BaseModel):
    reference: str
    tx_type: str
    direction: str
    amount_pkr: float
    counterparty_name: str
    description: str
    created_at: str


class TransactionDetail(TransactionItem):
    status: str
    topup_method: Optional[str] = None
    completed_at: Optional[str] = None


class TransactionListResponse(BaseModel):
    items: list[TransactionItem]
    total: int
    offset: int
    limit: int
    has_more: bool


class TypeBreakdown(BaseModel):
    tx_type: str
    count: int
    amount_pkr: float


class DailyBreakdown(BaseModel):
    date: str
    in_pkr: float
    out_pkr: float


class AnalyticsSummaryResponse(BaseModel):
    period: str
    total_in_pkr: float
    total_out_pkr: float
    net_pkr: float
    tx_count: int
    by_type: list[TypeBreakdown]
    daily: list[DailyBreakdown]


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except ValueError:
        return None


@router.get("/transactions", response_model=TransactionListResponse)
def list_transactions(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    tx_type: Optional[str] = Query(default=None, max_length=24),
    direction: Optional[str] = Query(default=None, pattern="^(in|out)$"),
    search: Optional[str] = Query(default=None, max_length=64),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
) -> TransactionListResponse:
    base = account_transactions_base(account.id)

    if tx_type:
        base = base.where(models.PalmPayTransaction.tx_type == tx_type.strip().lower())

    start = _parse_date(from_date)
    end = _parse_date(to_date)
    if start:
        base = base.where(models.PalmPayTransaction.created_at >= start)
    if end:
        base = base.where(models.PalmPayTransaction.created_at <= end)

    if search:
        q = f"%{search.strip()}%"
        base = base.where(
            or_(
                models.PalmPayTransaction.reference.ilike(q),
                models.PalmPayTransaction.description.ilike(q),
            )
        )

    if direction == "in":
        base = base.where(models.PalmPayTransaction.to_account_id == account.id)
    elif direction == "out":
        base = base.where(models.PalmPayTransaction.from_account_id == account.id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = int(db.execute(count_stmt).scalar_one())

    rows = db.execute(
        base.order_by(models.PalmPayTransaction.id.desc()).offset(offset).limit(limit)
    ).scalars().all()

    items = [TransactionItem(**{k: v for k, v in transaction_to_dict(db, account.id, tx).items() if k in TransactionItem.model_fields}) for tx in rows]

    return TransactionListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + len(items) < total,
    )


@router.get("/transactions/{reference}", response_model=TransactionDetail)
def get_transaction(
    reference: str,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> TransactionDetail:
    ref = reference.strip().upper()
    tx = db.execute(
        account_transactions_base(account.id).where(models.PalmPayTransaction.reference == ref)
    ).scalar_one_or_none()
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionDetail(**transaction_to_dict(db, account.id, tx))


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
    period: str = Query(default="week", pattern="^(week|month)$"),
) -> AnalyticsSummaryResponse:
    data = analytics_summary(db, account.id, period)
    return AnalyticsSummaryResponse(**data)
