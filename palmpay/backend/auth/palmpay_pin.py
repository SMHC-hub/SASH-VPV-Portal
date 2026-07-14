"""Spending PIN hashing for PalmPay wallet transfers."""
from __future__ import annotations

import hashlib
import hmac

DEFAULT_DEV_SPENDING_PIN = "1234"


def hash_spending_pin(pin: str) -> str:
    normalized = pin.strip()
    return hashlib.sha256(f"palmpay-pin:{normalized}".encode()).hexdigest()


def verify_spending_pin(pin: str, pin_hash: str | None) -> bool:
    if not pin_hash:
        return False
    return hmac.compare_digest(hash_spending_pin(pin), pin_hash)
