"""Optional email notifications for attendance events."""
from __future__ import annotations

import json
import logging
import smtplib
import urllib.error
import urllib.request
from datetime import timedelta
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth.attendance import get_settings, work_date_str
from backend.db import models
from backend.settings import (
    BREVO_API_KEY,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(SMTP_FROM and (SMTP_PASSWORD or BREVO_API_KEY))


def _send_via_brevo_api(*, to: str, subject: str, body: str, timeout_s: float) -> dict:
    api_key = (BREVO_API_KEY or "").strip()
    if not api_key:
        return {"sent": False, "reason": "brevo_api_not_configured"}
    payload = json.dumps(
        {
            "sender": {"email": SMTP_FROM, "name": "VeinPay"},
            "to": [{"email": to}],
            "subject": subject,
            "textContent": body,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key": api_key,
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            logger.info("Brevo API email sent to %s: %s", to, subject)
            return {"sent": True, "provider": "brevo_api", "raw": raw[:200]}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        logger.warning("Brevo API email failed to=%s status=%s body=%s", to, exc.code, detail[:300])
        low = detail.lower()
        if exc.code in (401, 403) and ("ip" in low or "unauthorized" in low):
            return {"sent": False, "reason": "smtp_ip_blocked", "detail": detail[:200]}
        return {"sent": False, "reason": "brevo_api_failed", "detail": detail[:200]}
    except Exception:
        logger.exception("Brevo API email error to %s", to)
        return {"sent": False, "reason": "brevo_api_failed"}


def _send_via_smtp(*, to: str, subject: str, body: str, timeout_s: float) -> dict:
    if not (SMTP_HOST and SMTP_PASSWORD):
        return {"sent": False, "reason": "smtp_not_configured"}
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    timeout = max(4.0, float(timeout_s))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=timeout) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to], msg.as_string())
        logger.info("SMTP email sent to %s: %s", to, subject)
        return {"sent": True, "provider": "smtp"}
    except smtplib.SMTPAuthenticationError as exc:
        logger.exception("SMTP authentication failed for user %s", SMTP_USER)
        err = str(exc.args[-1] if exc.args else exc).lower()
        if "unauthorized ip" in err or getattr(exc, "smtp_code", None) == 525:
            return {"sent": False, "reason": "smtp_ip_blocked"}
        return {"sent": False, "reason": "smtp_auth_failed"}
    except (TimeoutError, OSError, smtplib.SMTPException):
        logger.exception("SMTP error sending email to %s", to)
        return {"sent": False, "reason": "send_failed"}
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return {"sent": False, "reason": "send_failed"}


def send_email_detailed(*, to: str, subject: str, body: str, timeout_s: float = 12.0) -> dict:
    if not smtp_configured():
        logger.info("Email (not sent — SMTP not configured): to=%s subject=%s", to, subject)
        return {"sent": False, "reason": "smtp_not_configured"}
    if not to:
        return {"sent": False, "reason": "no_recipient"}

    if BREVO_API_KEY:
        api_result = _send_via_brevo_api(to=to, subject=subject, body=body, timeout_s=timeout_s)
        if api_result.get("sent"):
            return api_result

    smtp_result = _send_via_smtp(to=to, subject=subject, body=body, timeout_s=timeout_s)
    if smtp_result.get("sent"):
        return smtp_result

    if smtp_result.get("reason") == "smtp_ip_blocked" and BREVO_API_KEY:
        return _send_via_brevo_api(to=to, subject=subject, body=body, timeout_s=timeout_s)

    return smtp_result


def send_email(*, to: str, subject: str, body: str) -> bool:
    return send_email_detailed(to=to, subject=subject, body=body)["sent"]


def notify_absent(db: Session, *, account: models.Account, work_date: str) -> None:
    settings = get_settings(db)
    if not settings.notify_absent:
        return
    send_email(
        to=account.email,
        subject=f"Attendance: marked absent for {work_date}",
        body=(
            f"Hi {account.full_name},\n\n"
            f"You were marked absent for {work_date} because no check-in was recorded.\n"
            f"If this is incorrect, contact HR.\n"
        ),
    )


def get_primary_admin_email(db: Session) -> Optional[str]:
    admin = db.execute(
        select(models.Account).where(models.Account.role == "admin").order_by(models.Account.id)
    ).scalar_one_or_none()
    if admin and admin.email:
        return admin.email.strip()
    return None


def resolve_admin_notify_email(
    db: Session,
    *,
    preferred: Optional[str] = None,
    fallback_admin: Optional[models.Account] = None,
) -> Optional[str]:
    """HR / weekly-summary emails always go to the primary administrator account."""
    del preferred, fallback_admin
    return get_primary_admin_email(db)


def send_test_email(*, to: str) -> dict:
    if not to.strip():
        return {"sent": False, "reason": "no_recipient"}
    if not smtp_configured():
        send_email(
            to=to,
            subject="PalmVein test notification",
            body=(
                "This is a test message from PalmVein Workplace.\n\n"
                "SMTP is not configured on the server — this email was logged only, not delivered.\n"
            ),
        )
        return {"sent": False, "to": to, "reason": "smtp_not_configured"}
    result = send_email_detailed(
        to=to,
        subject="PalmVein test notification",
        body=(
            "This is a test message from PalmVein Workplace.\n\n"
            "If you received this, SMTP delivery is working correctly.\n"
        ),
    )
    return {"sent": result["sent"], "to": to, "reason": result.get("reason")}


def send_weekly_summary(db: Session, *, admin_email: Optional[str] = None) -> dict:
    settings = get_settings(db)
    to = resolve_admin_notify_email(db, preferred=admin_email)
    if not to:
        return {"sent": False, "reason": "no_admin_email"}

    from zoneinfo import ZoneInfo

    tz = ZoneInfo(settings.timezone)
    end = work_date_str(db)
    start = (datetime_from_iso(end) - timedelta(days=6)).isoformat()

    rows = db.execute(
        select(
            models.Account.full_name,
            models.AttendanceRecord.status,
            func.count(),
        )
        .join(models.AttendanceRecord, models.AttendanceRecord.account_id == models.Account.id)
        .where(
            models.Account.role == "employee",
            models.AttendanceRecord.work_date >= start,
            models.AttendanceRecord.work_date <= end,
        )
        .group_by(models.Account.full_name, models.AttendanceRecord.status)
        .order_by(models.Account.full_name)
    ).all()

    lines = [f"Weekly attendance summary ({start} to {end})", ""]
    if not rows:
        lines.append("No attendance records in this period.")
    else:
        current = ""
        for name, status, count in rows:
            if name != current:
                if current:
                    lines.append("")
                lines.append(f"{name}:")
                current = name
            lines.append(f"  {status}: {count}")

    body = "\n".join(lines) + f"\n\nTimezone: {settings.timezone}\n"
    result = send_email_detailed(
        to=to,
        subject=f"PalmVein weekly attendance ({start} – {end})",
        body=body,
    )
    return {
        "sent": result["sent"],
        "to": to,
        "date_from": start,
        "date_to": end,
        "reason": result.get("reason"),
    }


def datetime_from_iso(value: str):
    from datetime import date

    return date.fromisoformat(value)
