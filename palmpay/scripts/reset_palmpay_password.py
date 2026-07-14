#!/usr/bin/env python3
"""Set a PalmPay account password locally (dev recovery)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

from sqlalchemy import select, update

from backend.auth.passwords import hash_password
from backend.db.base import SessionLocal
from backend.db import models


def main() -> None:
    parser = argparse.ArgumentParser(description="Set PalmPay account password")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    email = args.email.strip().lower()
    db = SessionLocal()
    try:
        account = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.email == email)
        ).scalar_one_or_none()
        if account is None:
            print(f"ERROR: No PalmPay account for {email}")
            sys.exit(1)

        account.password_hash = hash_password(args.password)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.execute(
            update(models.PalmPayRefreshToken)
            .where(models.PalmPayRefreshToken.account_id == account.id)
            .where(models.PalmPayRefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        print(f"OK: password updated for {email} (phone {account.phone})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
