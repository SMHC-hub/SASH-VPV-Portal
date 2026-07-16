"""PalmPay login PIN routes — appended to palmpay_auth router."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.palmpay_login_pin import hash_login_pin, validate_login_pin, verify_login_pin
from backend.auth.palmpay_phone import normalize_pk_phone
from backend.auth.palmpay_pin import hash_spending_pin
from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.routes.palmpay_enrollment import _account_palm_enrolled
from backend.settings import (
    PALMPAY_LOCKOUT_MINUTES,
    PALMPAY_LOGIN_PIN_MAX_ATTEMPTS,
    PALMPAY_SIGNUP_OTP_WINDOW_S,
)

logger = logging.getLogger(__name__)


class AccountCheckResponse(BaseModel):
    exists: bool
    has_login_pin: bool
    onboarding_complete: bool
    phone_masked: str


class ConfirmOtpSignupRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=6, max_length=6)


class ConfirmOtpSignupResponse(BaseModel):
    success: bool
    phone: str
    message: str


class CompleteSignupRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    full_name: str = Field(min_length=2, max_length=128)
    login_pin: str = Field(min_length=4, max_length=4)
    use_same_pin_for_spending: bool = True


class LoginPinRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    login_pin: str = Field(min_length=4, max_length=4)


class SetLoginPinRequest(BaseModel):
    login_pin: str = Field(min_length=4, max_length=4)
    # Payment PIN used for transfers — default True so Google post-KYC setup sets it.
    use_same_pin_for_spending: bool = True


class ResetLoginPinRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=6, max_length=6)
    login_pin: str = Field(min_length=4, max_length=4)
    use_same_pin_for_spending: bool = True


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def register_login_pin_routes(router: APIRouter, helpers: dict) -> None:
    """Register Day-11 auth routes on the shared palmpay auth router."""

    issue_token_pair = helpers["issue_token_pair"]
    generate_wallet_number = helpers["generate_wallet_number"]
    validate_otp_code = helpers["validate_otp_code"]
    token_response = helpers["build_token_response"]

    def _onboarding_complete(db: Session, account: models.PalmPayAccount) -> bool:
        return account.kyc_status == "approved" and _account_palm_enrolled(db, account.id)

    def _recent_confirmed_otp(db: Session, phone: str) -> bool:
        window_start = _utcnow() - timedelta(seconds=PALMPAY_SIGNUP_OTP_WINDOW_S)
        row = db.execute(
            select(models.PalmPayOtpCode)
            .where(models.PalmPayOtpCode.phone == phone)
            .where(models.PalmPayOtpCode.used_at.isnot(None))
            .where(models.PalmPayOtpCode.used_at >= window_start)
            .order_by(models.PalmPayOtpCode.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        return row is not None

    @router.get("/account/check", response_model=AccountCheckResponse)
    def account_check(phone: str, db: Session = Depends(get_db)) -> AccountCheckResponse:
        from backend.auth.palmpay_phone import mask_phone

        normalized = normalize_pk_phone(phone)
        if normalized is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == normalized)
        ).scalar_one_or_none()

        if account is None:
            return AccountCheckResponse(
                exists=False,
                has_login_pin=False,
                onboarding_complete=False,
                phone_masked=mask_phone(normalized),
            )

        return AccountCheckResponse(
            exists=True,
            has_login_pin=bool(account.login_pin_hash),
            onboarding_complete=_onboarding_complete(db, account),
            phone_masked=mask_phone(normalized),
        )

    @router.post("/register/confirm-otp", response_model=ConfirmOtpSignupResponse)
    def confirm_otp_signup(
        payload: ConfirmOtpSignupRequest, db: Session = Depends(get_db)
    ) -> ConfirmOtpSignupResponse:
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        existing = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Phone already registered — log in instead")

        validate_otp_code(db, phone, payload.otp.strip(), account=None)
        db.commit()

        return ConfirmOtpSignupResponse(
            success=True,
            phone=phone,
            message="OTP confirmed — complete your account",
        )

    @router.post("/register/complete-signup", response_model=helpers["TokenResponse"])
    def complete_signup(payload: CompleteSignupRequest, db: Session = Depends(get_db)):
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        pin_error = validate_login_pin(payload.login_pin)
        if pin_error:
            raise HTTPException(status_code=400, detail=pin_error)

        existing = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Account already exists")

        if not _recent_confirmed_otp(db, phone):
            raise HTTPException(
                status_code=400,
                detail="OTP confirmation expired — verify your phone again",
            )

        account = models.PalmPayAccount(
            phone=phone,
            full_name=payload.full_name.strip(),
            login_pin_hash=hash_login_pin(payload.login_pin),
            login_pin_set_at=_utcnow(),
        )
        db.add(account)
        db.flush()

        spending_hash = (
            hash_spending_pin(payload.login_pin)
            if payload.use_same_pin_for_spending
            else None
        )
        wallet = models.PalmPayWallet(
            account_id=account.id,
            balance_pkr=0.0,
            account_number=generate_wallet_number(),
            spending_pin_hash=spending_hash,
        )
        db.add(wallet)
        db.flush()

        access, refresh = issue_token_pair(db, account)
        db.commit()
        db.refresh(account)
        db.refresh(wallet)

        logger.info("PalmPay signup complete for %s", phone)
        return token_response(
            account,
            wallet,
            access,
            refresh,
            needs_login_pin_setup=False,
            needs_spending_pin_setup=wallet.spending_pin_hash is None,
        )

    @router.post("/login/pin", response_model=helpers["TokenResponse"])
    def login_with_pin(payload: LoginPinRequest, db: Session = Depends(get_db)):
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()
        if account is None:
            raise HTTPException(status_code=404, detail="No account for this phone — sign up first")

        if account.login_locked_until and account.login_locked_until > _utcnow():
            remaining = int((account.login_locked_until - _utcnow()).total_seconds() // 60) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Too many wrong PIN attempts. Try again in {remaining} minutes.",
            )

        if not account.login_pin_hash:
            raise HTTPException(
                status_code=400,
                detail="Login PIN not set — use OTP or set your PIN",
            )

        if not verify_login_pin(payload.login_pin, account.login_pin_hash):
            account.failed_login_pin_attempts = int(account.failed_login_pin_attempts or 0) + 1
            if account.failed_login_pin_attempts >= PALMPAY_LOGIN_PIN_MAX_ATTEMPTS:
                account.login_locked_until = _utcnow() + timedelta(minutes=PALMPAY_LOCKOUT_MINUTES)
                account.failed_login_pin_attempts = 0
            db.commit()
            if account.login_locked_until and account.login_locked_until > _utcnow():
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many wrong PIN attempts. Locked for {PALMPAY_LOCKOUT_MINUTES} minutes.",
                )
            raise HTTPException(status_code=401, detail="Incorrect login PIN")

        account.failed_login_pin_attempts = 0
        account.login_locked_until = None

        wallet = account.wallet
        if wallet is None:
            wallet = models.PalmPayWallet(
                account_id=account.id,
                balance_pkr=0.0,
                account_number=generate_wallet_number(),
                spending_pin_hash=None,
            )
            db.add(wallet)
            db.flush()

        access, refresh = issue_token_pair(db, account)
        db.commit()
        db.refresh(wallet)

        return token_response(
            account,
            wallet,
            access,
            refresh,
            needs_login_pin_setup=False,
            needs_spending_pin_setup=wallet.spending_pin_hash is None,
        )

    @router.post("/pin/set", response_model=helpers["TokenResponse"])
    def set_login_pin(
        payload: SetLoginPinRequest,
        account: models.PalmPayAccount = Depends(get_current_palmpay_account),
        db: Session = Depends(get_db),
    ):
        pin_error = validate_login_pin(payload.login_pin)
        if pin_error:
            raise HTTPException(status_code=400, detail=pin_error)

        account.login_pin_hash = hash_login_pin(payload.login_pin)
        account.login_pin_set_at = _utcnow()
        account.failed_login_pin_attempts = 0
        account.login_locked_until = None

        wallet = account.wallet
        if wallet is None:
            wallet = models.PalmPayWallet(
                account_id=account.id,
                balance_pkr=0.0,
                account_number=generate_wallet_number(),
                spending_pin_hash=None,
            )
            db.add(wallet)
            db.flush()

        # Payment PIN for send-money — always set when requested (default True).
        if payload.use_same_pin_for_spending or wallet.spending_pin_hash is None:
            wallet.spending_pin_hash = hash_spending_pin(payload.login_pin)

        access, refresh = issue_token_pair(db, account)
        db.commit()
        db.refresh(account)
        db.refresh(wallet)
        return token_response(
            account,
            wallet,
            access,
            refresh,
            needs_login_pin_setup=False,
            needs_spending_pin_setup=wallet.spending_pin_hash is None,
        )

    @router.post("/pin/reset", response_model=helpers["TokenResponse"])
    def reset_login_pin(payload: ResetLoginPinRequest, db: Session = Depends(get_db)):
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        pin_error = validate_login_pin(payload.login_pin)
        if pin_error:
            raise HTTPException(status_code=400, detail=pin_error)

        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        validate_otp_code(db, phone, payload.otp.strip(), account=account)

        account.login_pin_hash = hash_login_pin(payload.login_pin)
        account.login_pin_set_at = _utcnow()
        account.failed_login_pin_attempts = 0
        account.login_locked_until = None
        account.failed_otp_attempts = 0
        account.locked_until = None

        wallet = account.wallet
        if wallet is None:
            wallet = models.PalmPayWallet(
                account_id=account.id,
                balance_pkr=0.0,
                account_number=generate_wallet_number(),
                spending_pin_hash=None,
            )
            db.add(wallet)
            db.flush()
        if payload.use_same_pin_for_spending or wallet.spending_pin_hash is None:
            wallet.spending_pin_hash = hash_spending_pin(payload.login_pin)

        access, refresh = issue_token_pair(db, account)
        db.commit()
        db.refresh(wallet)

        return token_response(
            account,
            wallet,
            access,
            refresh,
            needs_login_pin_setup=False,
            needs_spending_pin_setup=wallet.spending_pin_hash is None,
        )
