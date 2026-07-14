#!/usr/bin/env python3
"""Reset an account password from the command line (local recovery)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from backend.auth.passwords import hash_password
from backend.db.base import SessionLocal
from backend.db import models


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset account password locally")
    parser.add_argument("email", help="Account email")
    parser.add_argument("password", help="New password (min 8 chars)")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("ERROR: password must be at least 8 characters")
        sys.exit(1)

    db = SessionLocal()
    try:
        account = db.execute(
            select(models.Account).where(models.Account.email == args.email.lower().strip())
        ).scalar_one_or_none()
        if account is None:
            print(f"ERROR: no account for {args.email}")
            sys.exit(1)
        account.password_hash = hash_password(args.password)
        account.email_verified = True
        db.commit()
        print(f"OK: password updated for {account.full_name} ({account.email}) role={account.role}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
