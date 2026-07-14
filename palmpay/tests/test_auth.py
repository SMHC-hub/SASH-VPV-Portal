"""PalmPay auth API tests."""
from __future__ import annotations

from tests.conftest import auth_header, seed_account


def test_login_success_returns_tokens(client, db):
    seed_account(db, email="login@palmpay.pk", phone="03001111111")

    res = client.post(
        "/api/palmpay/auth/login/email",
        json={"email": "login@palmpay.pk", "password": "Test@Palmpay#1001"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["phone"] == "+923001111111"


def test_login_wrong_password_returns_401(client, db):
    seed_account(db, email="bad@palmpay.pk", phone="03002222222")

    res = client.post(
        "/api/palmpay/auth/login/email",
        json={"email": "bad@palmpay.pk", "password": "wrong-password"},
    )
    assert res.status_code == 401


def test_wallet_requires_auth(client):
    res = client.get("/api/palmpay/wallet")
    assert res.status_code == 401


def test_wallet_with_valid_token(auth_client, user):
    res = auth_client.get("/api/palmpay/wallet")
    assert res.status_code == 200
    body = res.json()
    assert body["balance_pkr"] == 5000.0
    assert body["account_number"]


def test_tampered_token_rejected(client, user):
    headers = auth_header(user)
    bad = headers["Authorization"][:-4] + "XXXX"
    res = client.get("/api/palmpay/wallet", headers={"Authorization": bad})
    assert res.status_code == 401
