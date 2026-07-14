"""PalmPay wallet API — extends the palm vein backend (SQLite, no PostgreSQL yet)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.routes.palmpay_enrollment import _account_palm_enrolled
from backend.settings import API_PORT, DB_PATH, PROJECT_ROOT

router = APIRouter(prefix="/api/palmpay", tags=["palmpay"])


class PalmPayHealthResponse(BaseModel):
    status: str
    service: str
    api_port: int
    database: str
    database_ok: bool
    redis_available: bool
    wallet_cache_enabled: bool
    wallet_cache_entries: int
    project_root: str
    wallet_enabled: bool
    message: str


class PalmPayProfileResponse(BaseModel):
    wallet_id: str | None
    balance_pkr: float
    kyc_status: str
    palm_enrolled: bool
    phone: str
    full_name: str
    message: str


@router.get("/health", response_model=PalmPayHealthResponse)
def palmpay_health(db: Session = Depends(get_db)) -> PalmPayHealthResponse:
    from backend.utils.wallet_cache import cache_stats

    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    cache = cache_stats()
    return PalmPayHealthResponse(
        status="ok" if db_ok else "degraded",
        service="palmpay",
        api_port=API_PORT,
        database=str(DB_PATH),
        database_ok=db_ok,
        redis_available=False,
        wallet_cache_enabled=True,
        wallet_cache_entries=cache["entries"],
        project_root=str(PROJECT_ROOT),
        wallet_enabled=True,
        message="PalmPay backend — Day 8 complete",
    )


@router.get("/profile", response_model=PalmPayProfileResponse)
def palmpay_profile(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> PalmPayProfileResponse:
    wallet = account.wallet
    enrolled = _account_palm_enrolled(db, account.id)

    return PalmPayProfileResponse(
        wallet_id=wallet.account_number if wallet else None,
        balance_pkr=float(wallet.balance_pkr) if wallet else 0.0,
        kyc_status=account.kyc_status,
        palm_enrolled=enrolled,
        phone=account.phone,
        full_name=account.full_name,
        message="Wallet profile loaded",
    )
