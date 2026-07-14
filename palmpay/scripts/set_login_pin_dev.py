#!/usr/bin/env python3
"""Dev helper — set login PIN for an existing PalmPay account."""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from backend.auth.palmpay_login_pin import hash_login_pin, validate_login_pin
from backend.auth.palmpay_phone import normalize_pk_phone
from backend.db import models
from backend.db.base import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Set PalmPay login PIN (dev)")
    parser.add_argument("--phone", required=True)
    parser.add_argument("--pin", required=True, help="6-digit login PIN")
    args = parser.parse_args()

    phone = normalize_pk_phone(args.phone)
    if phone is None:
        print("Invalid phone", file=sys.stderr)
        sys.exit(1)

    err = validate_login_pin(args.pin)
    if err:
        print(err, file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()
        if account is None:
            print("Account not found", file=sys.stderr)
            sys.exit(1)

        from datetime import datetime, timezone

        account.login_pin_hash = hash_login_pin(args.pin)
        account.login_pin_set_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        print(f"Login PIN set for {phone}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
