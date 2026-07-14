"""Palm Pay — kiosk payment requests, WebSocket results, notifications."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.palmpay_phone import normalize_pk_phone
from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.settings import (
    PALMPAY_DEV_OTP,
    PALMPAY_INTERNAL_SECRET,
    PALMPAY_KIOSK_DEVICE_TOKEN,
    PALMPAY_PAYMENT_REQUEST_TTL_S,
)
from backend.wallet import payment_hub
from backend.wallet.palmpay_payment_service import (
    create_payment_request,
    get_merchant_by_code,
    get_unread_notifications,
    list_active_merchants,
    mark_notification_read,
    process_palm_payment,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/palmpay", tags=["palmpay-payment"])


class MerchantItem(BaseModel):
    code: str
    name: str
    category: str


class PaymentRequestCreateBody(BaseModel):
    amount_pkr: float = Field(gt=0, le=500_000)
    merchant_code: str = Field(default="DEMO01", min_length=2, max_length=20)
    kiosk_id: str = Field(default="kiosk-dev", max_length=64)


class PaymentRequestCreateResponse(BaseModel):
    request_reference: str
    merchant_name: str
    amount_pkr: float
    expires_at: str
    expires_in_seconds: int
    stream_path: str


class ProcessPalmPaymentBody(BaseModel):
    request_reference: str = Field(min_length=8, max_length=32)
    account_id: int = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    scan_event_id: Optional[str] = Field(default=None, max_length=64)


class DevSimulateMatchBody(BaseModel):
    request_reference: str = Field(min_length=8, max_length=32)
    customer_phone: str = Field(min_length=10, max_length=20)
    confidence: float = Field(default=0.98, ge=0, le=1)


class NotificationItem(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    payload: dict
    created_at: str


def _require_kiosk_device(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Device "):
        raise HTTPException(status_code=401, detail="Kiosk device token required")
    token = authorization.removeprefix("Device ").strip()
    if token != PALMPAY_KIOSK_DEVICE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid kiosk device token")


def _require_internal_secret(x_internal_secret: str = Header(..., alias="X-Internal-Secret")) -> None:
    if x_internal_secret != PALMPAY_INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Invalid internal secret")


async def _broadcast_result(request_reference: str, payload: dict) -> None:
    await payment_hub.publish(request_reference, payload)


@router.get("/payment/merchants", response_model=list[MerchantItem])
def payment_merchants(db: Session = Depends(get_db)) -> list[MerchantItem]:
    merchants = list_active_merchants(db)
    return [
        MerchantItem(code=m.code, name=m.name, category=m.category)
        for m in merchants
    ]


@router.post("/payment/request/create", response_model=PaymentRequestCreateResponse)
def kiosk_create_payment_request(
    body: PaymentRequestCreateBody,
    db: Session = Depends(get_db),
    _: None = Depends(_require_kiosk_device),
) -> PaymentRequestCreateResponse:
    merchant = get_merchant_by_code(db, body.merchant_code)
    req = create_payment_request(
        db,
        merchant=merchant,
        amount_pkr=body.amount_pkr,
        kiosk_id=body.kiosk_id,
    )
    return PaymentRequestCreateResponse(
        request_reference=req.reference,
        merchant_name=merchant.name,
        amount_pkr=float(req.amount_pkr),
        expires_at=req.expires_at.isoformat(),
        expires_in_seconds=PALMPAY_PAYMENT_REQUEST_TTL_S,
        stream_path=f"/api/palmpay/payment/request/{req.reference}/stream",
    )


@router.websocket("/payment/request/{request_reference}/stream")
async def payment_request_stream(websocket: WebSocket, request_reference: str) -> None:
    auth = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if not auth or not auth.startswith("Device "):
        await websocket.close(code=4401)
        return
    token = auth.removeprefix("Device ").strip()
    if token != PALMPAY_KIOSK_DEVICE_TOKEN:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    ref = request_reference.strip().upper()
    queue = payment_hub.subscribe(ref)
    try:
        try:
            payload = await asyncio.wait_for(queue.get(), timeout=float(PALMPAY_PAYMENT_REQUEST_TTL_S + 15))
            await websocket.send_json(payload)
        except asyncio.TimeoutError:
            await websocket.send_json(
                {
                    "status": "timeout",
                    "success": False,
                    "failure_code": "timeout",
                    "failure_reason": "No palm scan received in time",
                    "request_reference": ref,
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        payment_hub.unsubscribe(ref, queue)


@router.post("/internal/palmpay/process")
async def internal_process_palm_payment(
    body: ProcessPalmPaymentBody,
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_secret),
) -> dict:
    result = process_palm_payment(
        db,
        request_reference=body.request_reference,
        payer_account_id=body.account_id,
        confidence=body.confidence,
        scan_event_id=body.scan_event_id,
    )
    payload = result.to_ws_payload()
    await _broadcast_result(body.request_reference, payload)
    return payload


@router.post("/payment/dev/simulate-match")
async def dev_simulate_palm_match(
    body: DevSimulateMatchBody,
    db: Session = Depends(get_db),
    _: None = Depends(_require_kiosk_device),
) -> dict:
    """Dev kiosk shortcut — match by phone instead of NIR scanner."""
    if not PALMPAY_DEV_OTP:
        raise HTTPException(status_code=403, detail="Dev simulate disabled")

    phone = normalize_pk_phone(body.customer_phone)
    if phone is None:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    account = db.execute(
        select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="Customer not registered on PalmPay")

    result = process_palm_payment(
        db,
        request_reference=body.request_reference,
        payer_account_id=account.id,
        confidence=body.confidence,
        scan_event_id="dev-simulate",
    )
    payload = result.to_ws_payload()
    await _broadcast_result(body.request_reference, payload)
    return payload


@router.get("/notifications/unread", response_model=list[NotificationItem])
def unread_notifications(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
    limit: int = 10,
) -> list[NotificationItem]:
    rows = get_unread_notifications(db, account.id, limit=limit)
    items: list[NotificationItem] = []
    for row in rows:
        try:
            payload = json.loads(row.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        items.append(
            NotificationItem(
                id=row.id,
                kind=row.kind,
                title=row.title,
                body=row.body,
                payload=payload,
                created_at=row.created_at.isoformat() if row.created_at else "",
            )
        )
    return items


@router.post("/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> dict:
    mark_notification_read(db, account.id, notification_id)
    return {"success": True}
