#!/usr/bin/env python3
"""Dev helper — credit a PalmPay wallet via JazzCash simulate API.

Usage:
  python scripts/dev_credit_wallet.py --phone 03180065367 --amount 2500000
"""
from __future__ import annotations

import argparse
import sys

try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_BASE = "http://127.0.0.1:8001"


def main() -> None:
    parser = argparse.ArgumentParser(description="Dev credit PalmPay wallet")
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--phone", required=True)
    parser.add_argument("--amount", type=float, default=2_500_000.0)
    args = parser.parse_args()

    base = args.base.rstrip("/")
    print(f"Sending OTP to {args.phone}...")
    reg = requests.post(
        f"{base}/api/palmpay/auth/register/phone",
        json={"phone": args.phone},
        timeout=15,
    )
    reg.raise_for_status()
    dev_otp = reg.json().get("dev_otp")
    if not dev_otp:
        print("dev_otp not returned — set PALMPAY_DEV_OTP=true on backend", file=sys.stderr)
        sys.exit(1)

    print("Verifying OTP...")
    auth = requests.post(
        f"{base}/api/palmpay/auth/register/verify-otp",
        json={"phone": args.phone, "otp": dev_otp},
        timeout=15,
    )
    auth.raise_for_status()
    token = auth.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Crediting PKR {args.amount:,.0f}...")
    topup = requests.post(
        f"{base}/api/palmpay/topup/jazzcash/simulate",
        json={"amount_pkr": args.amount},
        headers=headers,
        timeout=15,
    )
    topup.raise_for_status()
    data = topup.json()
    print(f"Done. New balance: PKR {data.get('new_balance_pkr', 0):,.2f}")


if __name__ == "__main__":
    main()
