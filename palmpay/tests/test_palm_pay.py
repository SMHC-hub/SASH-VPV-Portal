"""Palm Pay idempotency and concurrent payment tests."""
from __future__ import annotations

import threading

from sqlalchemy import func, select

from backend.db import models
from backend.settings import PALMPAY_PALM_MATCH_THRESHOLD
from backend.wallet.palmpay_payment_service import (
    create_payment_request,
    ensure_dev_merchant,
    process_palm_payment,
)
from tests.conftest import TestSessionLocal, seed_account


def test_double_process_same_request_is_idempotent(db):
    payer = seed_account(db, email="payer@palmpay.pk", phone="03006666666", balance=1000.0)
    merchant = ensure_dev_merchant(db)
    req = create_payment_request(
        db, merchant=merchant, amount_pkr=150.0, kiosk_id="KIOSK-1"
    )

    first = process_palm_payment(
        db,
        request_reference=req.reference,
        payer_account_id=payer.id,
        confidence=0.99,
    )
    second = process_palm_payment(
        db,
        request_reference=req.reference,
        payer_account_id=payer.id,
        confidence=0.99,
    )

    assert first.success is True
    assert second.success is True
    assert first.transaction_reference == second.transaction_reference

    tx_count = db.execute(
        select(func.count())
        .select_from(models.PalmPayTransaction)
        .where(models.PalmPayTransaction.idempotency_key == req.reference)
    ).scalar_one()
    assert tx_count == 1

    wallet = payer.wallet
    db.refresh(wallet)
    assert float(wallet.balance_pkr) == 850.0


def test_concurrent_palm_pay_only_one_transaction(db):
    payer = seed_account(db, email="race@palmpay.pk", phone="03007777777", balance=2000.0)
    merchant = ensure_dev_merchant(db)
    req = create_payment_request(
        db, merchant=merchant, amount_pkr=200.0, kiosk_id="KIOSK-2"
    )
    ref = req.reference
    results: list = []

    def _pay() -> None:
        session = TestSessionLocal()
        try:
            account = session.get(models.PalmPayAccount, payer.id)
            result = process_palm_payment(
                session,
                request_reference=ref,
                payer_account_id=account.id,
                confidence=0.98,
            )
            results.append(result)
        except Exception:
            results.append(None)
        finally:
            session.close()

    threads = [threading.Thread(target=_pay) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    successes = [r for r in results if r.success]
    assert len(successes) >= 1

    tx_count = db.execute(
        select(func.count())
        .select_from(models.PalmPayTransaction)
        .where(models.PalmPayTransaction.idempotency_key == ref)
    ).scalar_one()
    assert tx_count == 1

    db.refresh(payer.wallet)
    assert float(payer.wallet.balance_pkr) == 1800.0


def test_low_confidence_rejects_payment(db):
    payer = seed_account(db, email="low@palmpay.pk", phone="03008888888", balance=5000.0)
    merchant = ensure_dev_merchant(db)
    req = create_payment_request(
        db, merchant=merchant, amount_pkr=50.0, kiosk_id="KIOSK-3"
    )

    result = process_palm_payment(
        db,
        request_reference=req.reference,
        payer_account_id=payer.id,
        confidence=PALMPAY_PALM_MATCH_THRESHOLD - 0.01,
    )
    assert result.success is False
    assert result.failure_code == "low_confidence"


def test_frozen_wallet_rejects_palm_pay(db):
    payer = seed_account(
        db,
        email="frozenpay@palmpay.pk",
        phone="03009999999",
        balance=5000.0,
        frozen=True,
    )
    merchant = ensure_dev_merchant(db)
    req = create_payment_request(
        db, merchant=merchant, amount_pkr=50.0, kiosk_id="KIOSK-4"
    )

    result = process_palm_payment(
        db,
        request_reference=req.reference,
        payer_account_id=payer.id,
        confidence=0.99,
    )
    assert result.success is False
    assert result.failure_code == "wallet_frozen"
