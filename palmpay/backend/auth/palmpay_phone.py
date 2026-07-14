"""Pakistani mobile number normalization and validation."""
from __future__ import annotations

import re

_PHONE_RE = re.compile(r"^\+923\d{9}$")


def normalize_pk_phone(raw: str) -> str | None:
    """Normalize to E.164 +923XXXXXXXXX or return None if invalid."""
    digits = re.sub(r"\D", "", raw.strip())
    if digits.startswith("92") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) == 10 and digits.startswith("3"):
        normalized = f"+92{digits}"
        return normalized if _PHONE_RE.match(normalized) else None
    return None


def mask_phone(phone: str) -> str:
    if len(phone) < 8:
        return phone
    return f"{phone[:4]}***{phone[-3:]}"
