"""PalmPay phone OTP registration and JWT auth."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.auth.palmpay_phone import mask_phone, normalize_pk_phone
from backend.auth.palmpay_otp_delivery import issue_phone_otp, maybe_dev_otp
from backend.auth.passwords import hash_password
from backend.auth.palmpay_tokens import (
    create_palmpay_access_token,
    hash_refresh_token,
    issue_refresh_token,
    refresh_expires_at,
)
from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.settings import (
    PALMPAY_DEV_OTP,
    PALMPAY_LOCKOUT_MINUTES,
    PALMPAY_OTP_MAX_ATTEMPTS,
    PALMPAY_OTP_MAX_PER_HOUR,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/palmpay/auth", tags=["palmpay-auth"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_wallet_number() -> str:
    return f"PP{secrets.token_hex(4).upper()}"


def _issue_token_pair(db: Session, account: models.PalmPayAccount) -> tuple[str, str]:
    access = create_palmpay_access_token(account.id, account.phone)
    refresh = issue_refresh_token()
    db.add(
        models.PalmPayRefreshToken(
            account_id=account.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=refresh_expires_at(),
        )
    )
    return access, refresh


class PhoneRegisterRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)


class PhoneRegisterResponse(BaseModel):
    success: bool
    message: str
    phone_masked: str
    dev_otp: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=6, max_length=6)
    full_name: Optional[str] = Field(default=None, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    account_id: int
    phone: str
    email: str = ""
    full_name: str
    wallet_account_number: str
    balance_pkr: float
    needs_login_pin_setup: bool = False
    needs_spending_pin_setup: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class DeviceSessionItem(BaseModel):
    id: int
    device_name: str
    created_at: str
    expires_at: str
    status: str


class NotificationPreferencesResponse(BaseModel):
    transaction_notifications: bool
    security_notifications: bool
    promo_notifications: bool


class NotificationPreferencesUpdateRequest(BaseModel):
    transaction_notifications: Optional[bool] = None
    security_notifications: Optional[bool] = None
    promo_notifications: Optional[bool] = None


def _build_token_response(
    account: models.PalmPayAccount,
    wallet: models.PalmPayWallet,
    access: str,
    refresh: str,
    *,
    needs_login_pin_setup: bool = False,
    needs_spending_pin_setup: bool | None = None,
) -> TokenResponse:
    spending_needed = (
        needs_spending_pin_setup
        if needs_spending_pin_setup is not None
        else wallet.spending_pin_hash is None
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        account_id=account.id,
        phone=account.phone,
        email=account.email or "",
        full_name=account.full_name,
        wallet_account_number=wallet.account_number,
        balance_pkr=float(wallet.balance_pkr),
        needs_login_pin_setup=needs_login_pin_setup,
        needs_spending_pin_setup=bool(spending_needed),
    )


def _validate_otp_code(
    db: Session,
    phone: str,
    otp: str,
    account: models.PalmPayAccount | None,
) -> models.PalmPayOtpCode:
    if account and account.locked_until and account.locked_until > _utcnow():
        remaining = int((account.locked_until - _utcnow()).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Account locked. Try again in {remaining} minutes.",
        )

    otp_row = db.execute(
        select(models.PalmPayOtpCode)
        .where(models.PalmPayOtpCode.phone == phone)
        .where(models.PalmPayOtpCode.used_at.is_(None))
        .where(models.PalmPayOtpCode.expires_at > _utcnow())
        .order_by(models.PalmPayOtpCode.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    if otp_row is None or otp_row.code != otp.strip():
        if account is not None:
            account.failed_otp_attempts = int(account.failed_otp_attempts or 0) + 1
            if account.failed_otp_attempts >= PALMPAY_OTP_MAX_ATTEMPTS:
                account.locked_until = _utcnow() + timedelta(minutes=PALMPAY_LOCKOUT_MINUTES)
                account.failed_otp_attempts = 0
            db.commit()
            if account.locked_until and account.locked_until > _utcnow():
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many wrong OTP attempts. Locked for {PALMPAY_LOCKOUT_MINUTES} minutes.",
                )
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp_row.used_at = _utcnow()
    if account is not None:
        account.failed_otp_attempts = 0
        account.locked_until = None
    return otp_row


@router.post("/register/phone", response_model=PhoneRegisterResponse)
def register_phone(body: PhoneRegisterRequest, db: Session = Depends(get_db)) -> PhoneRegisterResponse:
    phone = normalize_pk_phone(body.phone)
    if phone is None:
        raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number (use 03XX XXXXXXX)")

    account = db.execute(
        select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
    ).scalar_one_or_none()
    if account and account.locked_until and account.locked_until > _utcnow():
        remaining = int((account.locked_until - _utcnow()).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Account locked. Try again in {remaining} minutes.",
        )

    hour_ago = _utcnow() - timedelta(hours=1)
    recent_count = db.execute(
        select(func.count())
        .select_from(models.PalmPayOtpCode)
        .where(models.PalmPayOtpCode.phone == phone)
        .where(models.PalmPayOtpCode.created_at >= hour_ago)
    ).scalar_one()
    if int(recent_count or 0) >= PALMPAY_OTP_MAX_PER_HOUR:
        raise HTTPException(status_code=429, detail="Too many OTP requests. Try again in an hour.")

    notify_email = account.email if account and account.email else None
    code, _ = issue_phone_otp(db, phone=phone, notify_email=notify_email)
    db.commit()

    logger.info(
        "PalmPay phone OTP issued for %s (dev=%s emailed=%s)",
        mask_phone(phone),
        PALMPAY_DEV_OTP,
        bool(notify_email),
    )

    return PhoneRegisterResponse(
        success=True,
        message=(
            "OTP sent to your email on file"
            if notify_email
            else "OTP issued"
        ),
        phone_masked=mask_phone(phone),
        dev_otp=maybe_dev_otp(code),
    )


@router.post("/register/verify-otp", response_model=TokenResponse)
def verify_otp(body: VerifyOtpRequest, db: Session = Depends(get_db)) -> TokenResponse:
    phone = normalize_pk_phone(body.phone)
    if phone is None:
        raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

    account = db.execute(
        select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
    ).scalar_one_or_none()

    _validate_otp_code(db, phone, body.otp, account)

    if account is None:
        account = models.PalmPayAccount(
            phone=phone,
            full_name=(body.full_name or "").strip() or "PalmPay User",
        )
        db.add(account)
        db.flush()
    else:
        if body.full_name and body.full_name.strip():
            account.full_name = body.full_name.strip()

    wallet = account.wallet
    if wallet is None:
        wallet = models.PalmPayWallet(
            account_id=account.id,
            balance_pkr=0.0,
            account_number=_generate_wallet_number(),
            spending_pin_hash=None,
        )
        db.add(wallet)
        db.flush()

    access, refresh = _issue_token_pair(db, account)
    db.commit()
    db.refresh(account)
    db.refresh(wallet)

    needs_pin = not bool(account.login_pin_hash)
    return _build_token_response(
        account,
        wallet,
        access,
        refresh,
        needs_login_pin_setup=needs_pin,
        needs_spending_pin_setup=wallet.spending_pin_hash is None,
    )


@router.post("/token/refresh", response_model=TokenResponse)
def refresh_tokens(body: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token_hash = hash_refresh_token(body.refresh_token)
    row = db.execute(
        select(models.PalmPayRefreshToken)
        .where(models.PalmPayRefreshToken.token_hash == token_hash)
        .where(models.PalmPayRefreshToken.revoked_at.is_(None))
        .where(models.PalmPayRefreshToken.expires_at > _utcnow())
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    account = db.get(models.PalmPayAccount, row.account_id)
    if account is None:
        raise HTTPException(status_code=401, detail="Account not found")

    row.revoked_at = _utcnow()
    wallet = account.wallet
    if wallet is None:
        wallet = models.PalmPayWallet(
            account_id=account.id,
            balance_pkr=0.0,
            account_number=_generate_wallet_number(),
            spending_pin_hash=None,
        )
        db.add(wallet)
        db.flush()

    access, refresh = _issue_token_pair(db, account)
    db.commit()
    db.refresh(wallet)

    return _build_token_response(account, wallet, access, refresh)


@router.get("/devices", response_model=list[DeviceSessionItem])
def list_auth_devices(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> list[DeviceSessionItem]:
    rows = db.execute(
        select(models.PalmPayRefreshToken)
        .where(models.PalmPayRefreshToken.account_id == account.id)
        .order_by(models.PalmPayRefreshToken.id.desc())
    ).scalars().all()

    items: list[DeviceSessionItem] = []
    for row in rows:
        if row.revoked_at is not None:
            status = "revoked"
        elif row.expires_at <= _utcnow():
            status = "expired"
        else:
            status = "active"
        items.append(
            DeviceSessionItem(
                id=row.id,
                device_name=f"PalmPay session #{row.id}",
                created_at=row.created_at.isoformat() if row.created_at else "",
                expires_at=row.expires_at.isoformat() if row.expires_at else "",
                status=status,
            )
        )
    return items


@router.delete("/devices/{session_id}")
def revoke_auth_device(
    session_id: int,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> dict:
    row = db.execute(
        select(models.PalmPayRefreshToken)
        .where(models.PalmPayRefreshToken.id == session_id)
        .where(models.PalmPayRefreshToken.account_id == account.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.revoked_at is None:
        row.revoked_at = _utcnow()
        db.commit()
    return {"success": True}


@router.get("/notifications/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
) -> NotificationPreferencesResponse:
    return NotificationPreferencesResponse(
        transaction_notifications=bool(account.notif_txn_enabled),
        security_notifications=bool(account.notif_security_enabled),
        promo_notifications=bool(account.notif_promo_enabled),
    )


@router.put("/notifications/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    body: NotificationPreferencesUpdateRequest,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    if body.transaction_notifications is not None:
        account.notif_txn_enabled = bool(body.transaction_notifications)
    if body.security_notifications is not None:
        account.notif_security_enabled = bool(body.security_notifications)
    if body.promo_notifications is not None:
        account.notif_promo_enabled = bool(body.promo_notifications)
    db.commit()
    db.refresh(account)
    return NotificationPreferencesResponse(
        transaction_notifications=bool(account.notif_txn_enabled),
        security_notifications=bool(account.notif_security_enabled),
        promo_notifications=bool(account.notif_promo_enabled),
    )


from backend.routes.palmpay_auth_login import register_login_pin_routes

register_login_pin_routes(
    router,
    {
        "issue_token_pair": _issue_token_pair,
        "generate_wallet_number": _generate_wallet_number,
        "validate_otp_code": _validate_otp_code,
        "build_token_response": _build_token_response,
        "TokenResponse": TokenResponse,
    },
)

from backend.routes.palmpay_auth_signup import register_email_auth_routes

register_email_auth_routes(
    router,
    {
        "issue_token_pair": _issue_token_pair,
        "generate_wallet_number": _generate_wallet_number,
        "build_token_response": _build_token_response,
        "TokenResponse": TokenResponse,
    },
)

from backend.routes.palmpay_auth_google import register_google_auth_routes

register_google_auth_routes(
    router,
    {
        "issue_token_pair": _issue_token_pair,
        "build_token_response": _build_token_response,
        "TokenResponse": TokenResponse,
    },
)
