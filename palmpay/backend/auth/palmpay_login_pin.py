"""Login PIN validation and hashing (app unlock — separate from spending PIN)."""
from __future__ import annotations

import re

from backend.auth.palmpay_pin import hash_spending_pin, verify_spending_pin

_LOGIN_PIN_RE = re.compile(r"^\d{4}$")
_WEAK_PINS = {
    "0000",
    "1111",
    "2222",
    "3333",
    "4444",
    "5555",
    "6666",
    "7777",
    "8888",
    "9999",
    "1234",
    "4321",
    "1212",
    "1122",
}


def validate_login_pin(pin: str) -> str | None:
    """Return error message if invalid, else None."""
    normalized = pin.strip()
    if not _LOGIN_PIN_RE.match(normalized):
        return "Login PIN must be exactly 4 digits"
    if normalized in _WEAK_PINS:
        return "Choose a stronger PIN — avoid repeated or sequential digits"
    return None


def hash_login_pin(pin: str) -> str:
    return hash_spending_pin(pin)


def verify_login_pin(pin: str, pin_hash: str | None) -> bool:
    return verify_spending_pin(pin, pin_hash)
