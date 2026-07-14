"""PalmPay access + refresh tokens."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.auth.jwt_tokens import _b64url, _b64url_decode
from backend.settings import AUTH_SECRET, PALMPAY_ACCESS_TTL_S, PALMPAY_REFRESH_TTL_S


def _sign_body(body: str) -> str:
    sig = hmac.new(AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return _b64url(sig)


def create_palmpay_access_token(account_id: int, phone: str) -> str:
    payload = {
        "sub": account_id,
        "phone": phone,
        "typ": "palmpay_access",
        "exp": int(time.time()) + PALMPAY_ACCESS_TTL_S,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign_body(body)}"


def decode_palmpay_access_token(token: str) -> dict[str, Any] | None:
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url(expected), sig):
        return None
    try:
        payload = json.loads(_b64url_decode(body))
    except (json.JSONDecodeError, ValueError):
        return None
    if payload.get("typ") != "palmpay_access":
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    return payload


def issue_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=PALMPAY_REFRESH_TTL_S)
