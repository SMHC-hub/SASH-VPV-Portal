"""PalmPay wallet and transfer tests."""
from __future__ import annotations

from tests.conftest import seed_account


def test_simulate_topup_increases_balance(auth_client, user, db):
    init = auth_client.post(
        "/api/palmpay/topup/jazzcash/initiate",
        json={"amount_pkr": 500},
    )
    assert init.status_code == 200
    order_ref = init.json()["order_reference"]

    sim = auth_client.post(
        "/api/palmpay/topup/jazzcash/simulate-existing",
        json={"order_reference": order_ref},
    )
    assert sim.status_code == 200
    assert sim.json()["new_balance_pkr"] == 5500.0


def test_frozen_wallet_blocks_topup(auth_client, db):
    frozen = seed_account(
        db,
        email="frozen@palmpay.pk",
        phone="03003333333",
        frozen=True,
    )
    from tests.conftest import auth_header

    client = auth_client
    client.headers.update(auth_header(frozen))

    res = client.post("/api/palmpay/topup/jazzcash/initiate", json={"amount_pkr": 200})
    assert res.status_code == 403


def test_transfer_to_recipient(auth_client, user, db):
    recipient = seed_account(
        db,
        email="peer@palmpay.pk",
        phone="03004444444",
        balance=100.0,
    )

    preview = auth_client.post(
        "/api/palmpay/transfer/initiate",
        json={
            "recipient_phone": "+923004444444",
            "amount_pkr": 250,
            "note": "lunch",
        },
    )
    assert preview.status_code == 200
    ref = preview.json()["transfer_reference"]

    confirm = auth_client.post(
        "/api/palmpay/transfer/confirm",
        json={"transfer_reference": ref, "spending_pin": "1234"},
    )
    assert confirm.status_code == 200
    assert confirm.json()["new_balance_pkr"] == 4750.0

    wallet = auth_client.get("/api/palmpay/wallet")
    assert wallet.json()["balance_pkr"] == 4750.0
