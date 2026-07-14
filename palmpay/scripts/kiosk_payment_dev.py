#!/usr/bin/env python3
"""Dev kiosk client — create payment request, simulate palm match (HTTP only).

Usage (backend must be running on port 8001):

  python scripts/kiosk_payment_dev.py --amount 250 --phone 03001234567
  python scripts/kiosk_payment_dev.py --base http://192.168.18.124:8001 --amount 250 --phone 03001234567

Requires PALMPAY_DEV_OTP=true and default kiosk token `palmpay-kiosk-dev`.
No extra pip packages required beyond `requests` (usually already installed).
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_BASE = "http://127.0.0.1:8001"
KIOSK_TOKEN = "palmpay-kiosk-dev"


def main() -> None:
    parser = argparse.ArgumentParser(description="PalmPay dev kiosk payment")
    parser.add_argument("--base", default=DEFAULT_BASE, help="API base URL")
    parser.add_argument("--amount", type=float, default=250.0, help="PKR amount")
    parser.add_argument("--phone", required=True, help="Customer phone (03XX...)")
    parser.add_argument("--merchant", default="DEMO01", help="Merchant code")
    parser.add_argument("--confidence", type=float, default=0.98, help="Match confidence 0-1")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    headers = {"Authorization": f"Device {KIOSK_TOKEN}"}

    print(f"Creating payment request for PKR {args.amount:,.0f} at {args.merchant}...")
    create_resp = requests.post(
        f"{base}/api/palmpay/payment/request/create",
        json={
            "amount_pkr": args.amount,
            "merchant_code": args.merchant,
            "kiosk_id": "kiosk-dev-script",
        },
        headers=headers,
        timeout=15,
    )
    create_resp.raise_for_status()
    req = create_resp.json()
    ref = req["request_reference"]
    print(f"Request {ref} — merchant: {req['merchant_name']}")

    print(f"Simulating palm match for {args.phone} (confidence={args.confidence})...")
    match_resp = requests.post(
        f"{base}/api/palmpay/payment/dev/simulate-match",
        json={
            "request_reference": ref,
            "customer_phone": args.phone,
            "confidence": args.confidence,
        },
        headers=headers,
        timeout=15,
    )
    match_resp.raise_for_status()
    api_result = match_resp.json()
    print("\nPayment result:")
    print(json.dumps(api_result, indent=2))

    if api_result.get("success"):
        print("\nOK — open the PalmPay app Scan tab to see the result screen.")
    elif api_result.get("failure_code") == "insufficient_balance":
        print("\nLow balance — use Load Money in the app to top up, then run again.")
    else:
        print(f"\nFailed: {api_result.get('failure_reason', 'unknown')}")


if __name__ == "__main__":
    main()
