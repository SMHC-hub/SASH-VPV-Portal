"""Quick PalmPay API benchmark (Day 8)."""
from __future__ import annotations

import statistics
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
PATH = "/api/palmpay/health"
REQUESTS = int(sys.argv[2]) if len(sys.argv) > 2 else 20


def main() -> None:
    durations: list[float] = []
    with httpx.Client(base_url=BASE, timeout=10.0) as client:
        for _ in range(REQUESTS):
            started = time.perf_counter()
            res = client.get(PATH)
            res.raise_for_status()
            durations.append((time.perf_counter() - started) * 1000)

    print(f"GET {PATH} x{REQUESTS}")
    print(f"  min: {min(durations):.1f} ms")
    print(f"  p50: {statistics.median(durations):.1f} ms")
    print(f"  max: {max(durations):.1f} ms")


if __name__ == "__main__":
    main()
