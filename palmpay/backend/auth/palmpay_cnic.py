"""Pakistani CNIC validation."""
from __future__ import annotations

import re

_CNIC_RE = re.compile(r"^\d{13}$")


def normalize_cnic(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw.strip())
    if not _CNIC_RE.match(digits):
        return None
    return digits


def format_cnic(digits: str) -> str:
    d = re.sub(r"\D", "", digits)
    if len(d) != 13:
        return digits
    return f"{d[0:5]}-{d[5:12]}-{d[12]}"
