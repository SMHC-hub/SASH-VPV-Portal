"""In-memory TTL cache for GET /wallet (Redis substitute in dev)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

_WALLET_TTL = timedelta(seconds=1)
_cache: dict[int, tuple[datetime, dict[str, Any]]] = {}
_lock = Lock()


def get_cached_wallet(account_id: int) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc)
    with _lock:
        entry = _cache.get(account_id)
        if entry is None:
            return None
        expires_at, payload = entry
        if now >= expires_at:
            del _cache[account_id]
            return None
        return payload


def set_cached_wallet(account_id: int, payload: dict[str, Any]) -> None:
    expires_at = datetime.now(timezone.utc) + _WALLET_TTL
    with _lock:
        _cache[account_id] = (expires_at, payload)


def invalidate_wallet_cache(account_id: int | None = None) -> None:
    with _lock:
        if account_id is None:
            _cache.clear()
        else:
            _cache.pop(account_id, None)


def cache_stats() -> dict[str, int]:
    with _lock:
        return {"entries": len(_cache)}
