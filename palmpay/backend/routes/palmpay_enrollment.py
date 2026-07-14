"""PalmPay palm enrollment sessions (mobile QR ↔ web kiosk)."""
from __future__ import annotations

import logging
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.auth.registration import complete_account_palm_enrollment
from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.routes.auth import get_register_session_for_finish, start_kiosk_palm_session_for_account
from backend.settings import FRONTEND_PUBLIC_URL, PALMPAY_ENROLL_DIR, PALMPAY_ENROLLMENT_TTL_S
from backend.shop.identity_link import ensure_web_account_for_palmpay

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/palmpay/palm", tags=["palmpay-palm"])
kiosk_router = APIRouter(prefix="/api/palmpay/kiosk", tags=["palmpay-kiosk"])


def _utcnow() -> datetime:
    """Naive UTC for SQLite DateTime columns (no tz stored)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is not None:
        expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    return expires_at < _utcnow()


def _account_palm_enrolled(db: Session, account_id: int) -> bool:
    row = db.execute(
        select(models.PalmPayPalmTemplate.id)
        .where(models.PalmPayPalmTemplate.account_id == account_id)
        .where(models.PalmPayPalmTemplate.is_active.is_(True))
        .limit(1)
    ).scalar_one_or_none()
    return row is not None


def _new_session_code() -> str:
    return secrets.token_hex(4).upper()


def _mask_phone(phone: str | None) -> str | None:
    if not phone or len(phone) < 4:
        return phone
    return f"{'*' * max(0, len(phone) - 4)}{phone[-4:]}"


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        return f"*@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def _get_pending_session(db: Session, code: str) -> models.PalmPayEnrollmentSession:
    sess = db.execute(
        select(models.PalmPayEnrollmentSession).where(
            models.PalmPayEnrollmentSession.session_code == code
        )
    ).scalar_one_or_none()
    if sess is None:
        raise HTTPException(status_code=404, detail="Enrollment session not found")
    if sess.status == "complete":
        raise HTTPException(status_code=400, detail="Session already completed")
    if sess.status != "pending" or _is_expired(sess.expires_at):
        if sess.status == "pending":
            sess.status = "expired"
            db.commit()
        raise HTTPException(
            status_code=410 if sess.status == "expired" else 400,
            detail=f"Session is {sess.status}",
        )
    return sess


def _write_palmpay_templates(
    db: Session,
    account: models.PalmPayAccount,
    code: str,
    left_paths: list[Path],
    right_paths: list[Path],
) -> None:
    db.execute(
        update(models.PalmPayPalmTemplate)
        .where(models.PalmPayPalmTemplate.account_id == account.id)
        .values(is_active=False)
    )
    enroll_dir = PALMPAY_ENROLL_DIR / str(account.id)
    enroll_dir.mkdir(parents=True, exist_ok=True)

    for hand, paths in (("left", left_paths), ("right", right_paths)):
        if not paths:
            continue
        dest = enroll_dir / f"{code}_{hand}.png"
        src = paths[-1]
        try:
            if src.is_file():
                shutil.copy2(str(src), str(dest))
        except OSError:
            dest.write_bytes(b"")
        db.add(
            models.PalmPayPalmTemplate(
                account_id=account.id,
                hand=hand,
                template_path=str(dest),
                is_active=True,
            )
        )


class EnrollmentInitResponse(BaseModel):
    session_code: str
    qr_payload: str
    expires_at: str
    message: str


class EnrollmentStatusResponse(BaseModel):
    status: str
    palm_enrolled: bool
    session_code: str | None = None
    message: str


class KioskCompleteRequest(BaseModel):
    session_code: str = Field(min_length=6, max_length=12)


class KioskCompleteResponse(BaseModel):
    success: bool
    account_id: int
    message: str


class KioskClaimRequest(BaseModel):
    session_code: str = Field(min_length=6, max_length=12)
    first_hand: Literal["Left", "Right"] = "Left"


class KioskClaimResponse(BaseModel):
    success: bool
    session_code: str
    display_name: str
    masked_phone: Optional[str] = None
    masked_email: Optional[str] = None
    register_session_id: str
    expires_at: str
    message: str


class KioskFinishRequest(BaseModel):
    session_code: str = Field(min_length=6, max_length=12)
    register_session_id: str = Field(min_length=8)


class KioskFinishResponse(BaseModel):
    success: bool
    account_id: int
    web_account_id: int
    message: str


@router.post("/enrollment/initiate", response_model=EnrollmentInitResponse)
def enrollment_initiate(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> EnrollmentInitResponse:
    if account.kyc_status != "approved":
        raise HTTPException(status_code=403, detail="Complete KYC before palm enrollment")

    db.execute(
        update(models.PalmPayEnrollmentSession)
        .where(models.PalmPayEnrollmentSession.account_id == account.id)
        .where(models.PalmPayEnrollmentSession.status == "pending")
        .values(status="expired")
    )

    code = _new_session_code()
    expires = _utcnow() + timedelta(seconds=PALMPAY_ENROLLMENT_TTL_S)
    db.add(
        models.PalmPayEnrollmentSession(
            account_id=account.id,
            session_code=code,
            status="pending",
            expires_at=expires,
        )
    )
    db.commit()

    # Prefer web kiosk deep-link so QR opens the enrollment page with the code
    qr_payload = f"{FRONTEND_PUBLIC_URL}/kiosk/enroll?code={code}"
    return EnrollmentInitResponse(
        session_code=code,
        qr_payload=qr_payload,
        expires_at=expires.isoformat(),
        message="Show this code or QR at the web enrollment kiosk",
    )


@router.get("/enrollment/status", response_model=EnrollmentStatusResponse)
def enrollment_status(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> EnrollmentStatusResponse:
    enrolled = _account_palm_enrolled(db, account.id)
    if enrolled:
        return EnrollmentStatusResponse(
            status="complete",
            palm_enrolled=True,
            message="Palm enrolled successfully",
        )

    sess = db.execute(
        select(models.PalmPayEnrollmentSession)
        .where(models.PalmPayEnrollmentSession.account_id == account.id)
        .order_by(models.PalmPayEnrollmentSession.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    if sess is None:
        return EnrollmentStatusResponse(
            status="not_started",
            palm_enrolled=False,
            message="Start enrollment to get a kiosk QR code",
        )

    if sess.status == "complete":
        return EnrollmentStatusResponse(
            status="complete",
            palm_enrolled=True,
            session_code=sess.session_code,
            message="Enrollment complete",
        )

    if _is_expired(sess.expires_at) and sess.status == "pending":
        sess.status = "expired"
        db.commit()
        return EnrollmentStatusResponse(
            status="expired",
            palm_enrolled=False,
            session_code=sess.session_code,
            message="Session expired — tap to start again",
        )

    return EnrollmentStatusResponse(
        status=sess.status,
        palm_enrolled=False,
        session_code=sess.session_code,
        message="Waiting for kiosk scan…",
    )


@kiosk_router.post("/enrollment/claim", response_model=KioskClaimResponse)
def kiosk_enrollment_claim(
    body: KioskClaimRequest,
    db: Session = Depends(get_db),
) -> KioskClaimResponse:
    """Web kiosk: look up mobile enrollment code and open NIR capture session."""
    code = body.session_code.strip().upper()
    sess = _get_pending_session(db, code)
    pp = db.get(models.PalmPayAccount, sess.account_id)
    if pp is None:
        raise HTTPException(status_code=404, detail="Account not found")

    web = ensure_web_account_for_palmpay(db, pp, commit=True)
    status = start_kiosk_palm_session_for_account(
        web,
        first_hand=body.first_hand,
        palmpay_enrollment_code=code,
    )
    name = (pp.full_name or web.full_name or "Customer").strip() or "Customer"
    return KioskClaimResponse(
        success=True,
        session_code=code,
        display_name=name,
        masked_phone=_mask_phone(pp.phone),
        masked_email=_mask_email(pp.email or web.email),
        register_session_id=status["register_session_id"],
        expires_at=sess.expires_at.isoformat(),
        message=f"Ready to enroll palm for {name}",
    )


@kiosk_router.post("/enrollment/finish", response_model=KioskFinishResponse)
def kiosk_enrollment_finish(
    body: KioskFinishRequest,
    db: Session = Depends(get_db),
) -> KioskFinishResponse:
    """After both hands captured on web kiosk — persist templates + notify mobile."""
    code = body.session_code.strip().upper()
    sess = _get_pending_session(db, code)
    pp = db.get(models.PalmPayAccount, sess.account_id)
    if pp is None:
        raise HTTPException(status_code=404, detail="Account not found")

    reg = get_register_session_for_finish(body.register_session_id)
    if reg.palmpay_enrollment_code and reg.palmpay_enrollment_code.upper() != code:
        raise HTTPException(status_code=400, detail="Capture session does not match this code")
    if not reg.both_complete:
        raise HTTPException(status_code=400, detail="Complete both hands before finishing")
    if not reg.existing_account_id:
        raise HTTPException(status_code=400, detail="Invalid capture session")

    web = db.get(models.Account, reg.existing_account_id)
    if web is None:
        raise HTTPException(status_code=404, detail="Web account not found")

    try:
        complete_account_palm_enrollment(
            db,
            web,
            left_embeddings=reg.left_embeddings,
            right_embeddings=reg.right_embeddings,
            left_paths=reg.left_paths,
            right_paths=reg.right_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _write_palmpay_templates(db, pp, code, reg.left_paths, reg.right_paths)
    sess.status = "complete"
    sess.completed_at = _utcnow()
    db.commit()

    logger.info(
        "Kiosk enrollment finish palmpay=%s web=%s session=%s",
        pp.id,
        web.id,
        code,
    )
    return KioskFinishResponse(
        success=True,
        account_id=pp.id,
        web_account_id=web.id,
        message="Palm enrolled — mobile app will update automatically",
    )


@kiosk_router.post("/enrollment/complete", response_model=KioskCompleteResponse)
def kiosk_enrollment_complete(
    body: KioskCompleteRequest,
    db: Session = Depends(get_db),
) -> KioskCompleteResponse:
    """Dev / simulate: mark session complete without NIR capture."""
    code = body.session_code.strip().upper()
    sess = _get_pending_session(db, code)

    account = db.get(models.PalmPayAccount, sess.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    # Ensure web link exists for shop checkout later
    try:
        ensure_web_account_for_palmpay(db, account, commit=False)
    except Exception:
        logger.exception("Web account provision skipped for simulate enroll")

    db.execute(
        update(models.PalmPayPalmTemplate)
        .where(models.PalmPayPalmTemplate.account_id == account.id)
        .values(is_active=False)
    )

    enroll_dir = PALMPAY_ENROLL_DIR / str(account.id)
    enroll_dir.mkdir(parents=True, exist_ok=True)
    template_path = str(enroll_dir / f"{code}_right.dat")

    db.add(
        models.PalmPayPalmTemplate(
            account_id=account.id,
            hand="right",
            template_path=template_path,
            is_active=True,
        )
    )
    sess.status = "complete"
    sess.completed_at = _utcnow()
    db.commit()

    logger.info("Palm enrollment complete (stub) account=%s session=%s", account.id, code)

    return KioskCompleteResponse(
        success=True,
        account_id=account.id,
        message="Palm template enrolled",
    )
