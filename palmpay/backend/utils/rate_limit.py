"""In-memory rate limiting for PalmPay API (Redis substitute in dev)."""
from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("palmpay.ratelimit")

# Default: 120 requests / minute per client IP on /api/palmpay/*
_DEFAULT_LIMIT = 120
_DEFAULT_WINDOW_SEC = 60

# Sensitive auth endpoints: 20 / hour per IP
_STRICT_PATHS: dict[str, tuple[int, int]] = {
    "/api/palmpay/auth/password/forgot": (20, 3600),
    "/api/palmpay/auth/register/signup-start": (20, 3600),
    "/api/palmpay/auth/login/email": (60, 3600),
}

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def _client_key(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def _limit_for(path: str) -> tuple[int, int]:
    for prefix, limit in _STRICT_PATHS.items():
        if path.startswith(prefix):
            return limit
    return _DEFAULT_LIMIT, _DEFAULT_WINDOW_SEC


def check_rate_limit(key: str, path: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds)."""
    max_hits, window_sec = _limit_for(path)
    bucket = f"{key}:{path.split('?')[0]}"
    now = time.monotonic()
    cutoff = now - window_sec

    with _lock:
        dq = _hits[bucket]
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= max_hits:
            retry_after = max(1, int(window_sec - (now - dq[0])))
            return False, retry_after
        dq.append(now)
        return True, 0


class PalmPayRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if not path.startswith("/api/palmpay"):
            return await call_next(request)

        allowed, retry_after = check_rate_limit(_client_key(request), path)
        if not allowed:
            logger.warning(
                json.dumps(
                    {
                        "event": "rate_limited",
                        "path": path,
                        "client": _client_key(request),
                        "retry_after_sec": retry_after,
                    },
                    separators=(",", ":"),
                )
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait and try again."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
