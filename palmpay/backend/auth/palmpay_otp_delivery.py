"""PalmPay OTP delivery via SMTP (email). Phone codes are emailed until SMS is configured."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.auth.notifications import send_email_detailed, smtp_configured
from backend.db import models
from backend.settings import PALMPAY_DEV_OTP, PALMPAY_OTP_TTL_S

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def maybe_dev_otp(code: str) -> Optional[str]:
    return code if PALMPAY_DEV_OTP else None


def require_smtp_or_dev() -> None:
    if smtp_configured() or PALMPAY_DEV_OTP:
        return
    raise HTTPException(
        status_code=503,
        detail="Email delivery is not configured. Set SMTP_* env vars on the server.",
    )


def issue_email_otp(
    db: Session,
    *,
    email: str,
    subject: str,
    body_prefix: str,
    fail_if_not_sent: bool = True,
) -> tuple[str, dict]:
    """Store email OTP and deliver via SMTP. Returns (code, send_result)."""
    require_smtp_or_dev()
    email_l = email.lower().strip()
    code = generate_otp()
    db.add(
        models.PalmPayEmailOtpCode(
            email=email_l,
            code=code,
            expires_at=_utcnow() + timedelta(seconds=PALMPAY_OTP_TTL_S),
        )
    )
    body = (
        f"{body_prefix}\n\n"
        f"Your VeinPay code: {code}\n\n"
        f"It expires in {max(1, PALMPAY_OTP_TTL_S // 60)} minutes. "
        f"If you did not request this, ignore this email.\n"
    )
    result: dict = {"sent": False, "reason": "skipped_dev"}
    if smtp_configured():
        result = send_email_detailed(to=email_l, subject=subject, body=body)
        if result.get("sent"):
            logger.info("PalmPay email OTP sent to=%s", email_l)
        else:
            logger.warning(
                "PalmPay email OTP not sent to=%s reason=%s",
                email_l,
                result.get("reason"),
            )
            if fail_if_not_sent and not PALMPAY_DEV_OTP:
                raise HTTPException(
                    status_code=503,
                    detail=_smtp_user_message(result.get("reason")),
                )
    elif PALMPAY_DEV_OTP:
        logger.info("PalmPay DEV email OTP for %s: %s", email_l, code)
    return code, result


def issue_phone_otp(
    db: Session,
    *,
    phone: str,
    notify_email: Optional[str] = None,
    fail_if_not_sent: bool = True,
) -> tuple[str, dict]:
    """
    Store phone OTP. Deliver via email to notify_email (no SMS gateway yet).
    In DEV mode without SMTP, code is only logged / returned via maybe_dev_otp.
    """
    code = generate_otp()
    db.add(
        models.PalmPayOtpCode(
            phone=phone,
            code=code,
            expires_at=_utcnow() + timedelta(seconds=PALMPAY_OTP_TTL_S),
        )
    )
    result: dict = {"sent": False, "reason": "no_notify_email"}
    email = (notify_email or "").strip().lower()
    if email and smtp_configured():
        result = send_email_detailed(
            to=email,
            subject="VeinPay phone verification code",
            body=(
                f"Your VeinPay phone verification code for {phone} is: {code}\n\n"
                f"Expires in {max(1, PALMPAY_OTP_TTL_S // 60)} minutes.\n"
                f"(Delivered by email until SMS is enabled.)\n"
            ),
        )
        if result.get("sent"):
            logger.info("PalmPay phone OTP emailed to=%s phone=%s", email, phone)
        else:
            logger.warning(
                "PalmPay phone OTP email failed to=%s reason=%s",
                email,
                result.get("reason"),
            )
            if fail_if_not_sent and not PALMPAY_DEV_OTP:
                raise HTTPException(
                    status_code=503,
                    detail=_smtp_user_message(result.get("reason")),
                )
    elif email and PALMPAY_DEV_OTP:
        logger.info("PalmPay DEV phone OTP for %s (email %s): %s", phone, email, code)
        result = {"sent": False, "reason": "skipped_dev"}
    elif PALMPAY_DEV_OTP:
        logger.info("PalmPay DEV phone OTP for %s: %s", phone, code)
        result = {"sent": False, "reason": "skipped_dev"}
    else:
        if not email:
            raise HTTPException(
                status_code=503,
                detail="Cannot deliver phone OTP without an email on file (SMS not configured).",
            )
        require_smtp_or_dev()
    return code, result


def _smtp_user_message(reason: Optional[str]) -> str:
    if reason == "smtp_ip_blocked":
        return "Email provider blocked this server IP. Check Brevo authorized IPs."
    if reason == "smtp_auth_failed":
        return "Email login failed. Check SMTP credentials."
    if reason == "smtp_not_configured":
        return "Email delivery is not configured on the server."
    return "Could not send verification email. Try again in a moment."
