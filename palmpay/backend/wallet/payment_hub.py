"""In-memory pub/sub for kiosk WebSocket payment results (dev — no Redis)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

_subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}


def subscribe(request_reference: str) -> asyncio.Queue[dict[str, Any]]:
    ref = request_reference.strip().upper()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1)
    _subscribers.setdefault(ref, []).append(queue)
    return queue


def unsubscribe(request_reference: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
    ref = request_reference.strip().upper()
    listeners = _subscribers.get(ref)
    if not listeners:
        return
    try:
        listeners.remove(queue)
    except ValueError:
        pass
    if not listeners:
        _subscribers.pop(ref, None)


async def publish(request_reference: str, payload: dict[str, Any]) -> None:
    ref = request_reference.strip().upper()
    listeners = list(_subscribers.get(ref, []))
    if not listeners:
        logger.debug("No WebSocket listeners for payment request %s", ref)
        return
    for queue in listeners:
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass
    _subscribers.pop(ref, None)
