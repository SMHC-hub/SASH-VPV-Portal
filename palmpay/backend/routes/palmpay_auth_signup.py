"""PalmPay email/password signup and login routes."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from backend.auth.palmpay_login_pin import hash_login_pin, validate_login_pin
from backend.auth.palmpay_phone import normalize_pk_phone
from backend.auth.palmpay_pin import hash_spending_pin
from backend.auth.passwords import hash_password, verify_password
from backend.db import models
from backend.deps import get_db
from backend.settings import PALMPAY_DEV_OTP, PALMPAY_DEV_SPENDING_PIN, PALMPAY_OTP_TTL_S

logger = logging.getLogger(__name__)

_SIGNUP_TTL_MINUTES = 30


class SignupStartRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=128)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class SignupStartResponse(BaseModel):
    success: bool
    phone: str
    email: str
    message: str
    dev_otp_phone: Optional[str] = None
    dev_otp_email: Optional[str] = None


class VerifyPhoneSignupRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=6, max_length=6)


class VerifyEmailSignupRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class FinishSignupRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    email: EmailStr
    login_pin: str = Field(min_length=4, max_length=4)


class FinishSignupResponse(BaseModel):
    success: bool
    message: str


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool
    email: str
    message: str
    dev_otp: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def _issue_phone_otp(db: Session, phone: str) -> Optional[str]:
    code = _generate_otp()
    db.add(
        models.PalmPayOtpCode(
            phone=phone,
            code=code,
            expires_at=_utcnow() + timedelta(seconds=PALMPAY_OTP_TTL_S),
        )
    )
    return code if PALMPAY_DEV_OTP else None


def _issue_email_otp(db: Session, email: str) -> Optional[str]:
    code = _generate_otp()
    db.add(
        models.PalmPayEmailOtpCode(
            email=email,
            code=code,
            expires_at=_utcnow() + timedelta(seconds=PALMPAY_OTP_TTL_S),
        )
    )
    return code if PALMPAY_DEV_OTP else None


def _validate_phone_otp(db: Session, phone: str, otp: str) -> None:
    row = db.execute(
        select(models.PalmPayOtpCode)
        .where(models.PalmPayOtpCode.phone == phone)
        .where(models.PalmPayOtpCode.used_at.is_(None))
        .where(models.PalmPayOtpCode.expires_at > _utcnow())
        .order_by(models.PalmPayOtpCode.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None or row.code != otp.strip():
        raise HTTPException(status_code=400, detail="Invalid or expired phone OTP")
    row.used_at = _utcnow()


def _validate_email_otp(db: Session, email: str, otp: str) -> None:
    row = db.execute(
        select(models.PalmPayEmailOtpCode)
        .where(models.PalmPayEmailOtpCode.email == email)
        .where(models.PalmPayEmailOtpCode.used_at.is_(None))
        .where(models.PalmPayEmailOtpCode.expires_at > _utcnow())
        .order_by(models.PalmPayEmailOtpCode.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None or row.code != otp.strip():
        raise HTTPException(status_code=400, detail="Invalid or expired email OTP")
    row.used_at = _utcnow()


def register_email_auth_routes(router: APIRouter, helpers: dict) -> None:
    issue_token_pair = helpers["issue_token_pair"]
    generate_wallet_number = helpers["generate_wallet_number"]
    token_response = helpers["build_token_response"]

    @router.post("/register/signup-start", response_model=SignupStartResponse)
    def signup_start(payload: SignupStartRequest, db: Session = Depends(get_db)) -> SignupStartResponse:
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        email = payload.email.lower().strip()

        if db.execute(select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Phone already registered — log in instead")
        if db.execute(select(models.PalmPayAccount).where(models.PalmPayAccount.email == email)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered — log in instead")

        db.execute(delete(models.PalmPaySignupDraft).where(models.PalmPaySignupDraft.phone == phone))
        db.execute(delete(models.PalmPaySignupDraft).where(models.PalmPaySignupDraft.email == email))

        draft = models.PalmPaySignupDraft(
            phone=phone,
            email=email,
            full_name=payload.full_name.strip(),
            password_hash=hash_password(payload.password),
            expires_at=_utcnow() + timedelta(minutes=_SIGNUP_TTL_MINUTES),
        )
        db.add(draft)

        dev_phone = _issue_phone_otp(db, phone)
        dev_email = _issue_email_otp(db, email)
        db.commit()

        return SignupStartResponse(
            success=True,
            phone=phone,
            email=email,
            message="Verification codes sent to your phone and email",
            dev_otp_phone=dev_phone,
            dev_otp_email=dev_email,
        )

    @router.post("/register/verify-phone-signup")
    def verify_phone_signup(payload: VerifyPhoneSignupRequest, db: Session = Depends(get_db)) -> dict:
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        draft = db.execute(
            select(models.PalmPaySignupDraft).where(models.PalmPaySignupDraft.phone == phone)
        ).scalar_one_or_none()
        if draft is None or draft.expires_at < _utcnow():
            raise HTTPException(status_code=400, detail="Signup session expired — start again")

        _validate_phone_otp(db, phone, payload.otp)
        draft.phone_verified = True
        db.commit()
        return {"success": True, "message": "Phone verified"}

    @router.post("/register/verify-email-signup")
    def verify_email_signup(payload: VerifyEmailSignupRequest, db: Session = Depends(get_db)) -> dict:
        email = payload.email.lower().strip()
        draft = db.execute(
            select(models.PalmPaySignupDraft).where(models.PalmPaySignupDraft.email == email)
        ).scalar_one_or_none()
        if draft is None or draft.expires_at < _utcnow():
            raise HTTPException(status_code=400, detail="Signup session expired — start again")

        _validate_email_otp(db, email, payload.otp)
        draft.email_verified = True
        db.commit()
        return {"success": True, "message": "Email verified"}

    @router.post("/register/finish-signup", response_model=FinishSignupResponse)
    def finish_signup(payload: FinishSignupRequest, db: Session = Depends(get_db)) -> FinishSignupResponse:
        phone = normalize_pk_phone(payload.phone)
        if phone is None:
            raise HTTPException(status_code=400, detail="Invalid Pakistani mobile number")

        email = payload.email.lower().strip()
        pin_error = validate_login_pin(payload.login_pin)
        if pin_error:
            raise HTTPException(status_code=400, detail=pin_error)

        draft = db.execute(
            select(models.PalmPaySignupDraft)
            .where(models.PalmPaySignupDraft.phone == phone)
            .where(models.PalmPaySignupDraft.email == email)
        ).scalar_one_or_none()
        if draft is None or draft.expires_at < _utcnow():
            raise HTTPException(status_code=400, detail="Signup session expired — start again")
        if not draft.phone_verified or not draft.email_verified:
            raise HTTPException(status_code=400, detail="Verify your phone and email before creating PIN")

        account = models.PalmPayAccount(
            phone=phone,
            email=email,
            password_hash=draft.password_hash,
            email_verified=True,
            phone_verified=True,
            full_name=draft.full_name,
            login_pin_hash=hash_login_pin(payload.login_pin),
            login_pin_set_at=_utcnow(),
        )
        db.add(account)
        db.flush()

        wallet = models.PalmPayWallet(
            account_id=account.id,
            balance_pkr=0.0,
            account_number=generate_wallet_number(),
            spending_pin_hash=hash_spending_pin(PALMPAY_DEV_SPENDING_PIN),
        )
        db.add(wallet)
        db.delete(draft)
        db.flush()
        try:
            from backend.shop.identity_link import link_web_accounts_matching_palmpay

            link_web_accounts_matching_palmpay(db, account, commit=False)
        except Exception:
            logger.exception("Web↔PalmPay reverse link failed for %s", email)
        db.commit()

        logger.info("PalmPay email signup complete for %s", email)
        return FinishSignupResponse(
            success=True,
            message="Account created — log in with your email and password",
        )

    @router.post("/login/email", response_model=helpers["TokenResponse"])
    def login_with_email(payload: EmailLoginRequest, db: Session = Depends(get_db)):
        email = payload.email.lower().strip()
        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.email == email)
        ).scalar_one_or_none()
        if account is None or not account.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(payload.password, account.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        wallet = account.wallet
        if wallet is None:
            wallet = models.PalmPayWallet(
                account_id=account.id,
                balance_pkr=0.0,
                account_number=generate_wallet_number(),
                spending_pin_hash=hash_spending_pin(PALMPAY_DEV_SPENDING_PIN),
            )
            db.add(wallet)
            db.flush()

        access, refresh = issue_token_pair(db, account)
        try:
            from backend.shop.identity_link import link_web_accounts_matching_palmpay

            link_web_accounts_matching_palmpay(db, account, commit=False)
        except Exception:
            logger.exception("Web↔PalmPay reverse link failed on email login for %s", email)
        db.commit()
        db.refresh(wallet)
        return token_response(account, wallet, access, refresh, needs_login_pin_setup=False)

    @router.post("/password/forgot", response_model=ForgotPasswordResponse)
    def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
        email = payload.email.lower().strip()
        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.email == email)
        ).scalar_one_or_none()
        if account is None or not account.password_hash:
            raise HTTPException(
                status_code=404,
                detail="No account with this email — sign up first",
            )

        dev_otp = _issue_email_otp(db, email)
        db.commit()

        return ForgotPasswordResponse(
            success=True,
            email=email,
            message="Reset code sent to your email",
            dev_otp=dev_otp,
        )

    @router.post("/password/reset", response_model=ResetPasswordResponse)
    def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> ResetPasswordResponse:
        email = payload.email.lower().strip()
        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.email == email)
        ).scalar_one_or_none()
        if account is None or not account.password_hash:
            raise HTTPException(status_code=404, detail="Account not found")

        _validate_email_otp(db, email, payload.otp)
        account.password_hash = hash_password(payload.new_password)
        db.execute(
            update(models.PalmPayRefreshToken)
            .where(models.PalmPayRefreshToken.account_id == account.id)
            .where(models.PalmPayRefreshToken.revoked_at.is_(None))
            .values(revoked_at=_utcnow())
        )
        db.commit()

        logger.info("PalmPay password reset for %s", email)
        return ResetPasswordResponse(
            success=True,
            message="Password updated — log in with your new password",
        )
