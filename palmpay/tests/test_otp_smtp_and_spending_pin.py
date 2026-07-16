"""OTP SMTP delivery + spending PIN setup tests (email send mocked)."""
from __future__ import annotations

import re
from unittest.mock import patch

from backend.auth.palmpay_pin import hash_spending_pin
from backend.settings import PALMPAY_DEV_SPENDING_PIN
from tests.conftest import auth_header, seed_account


def test_signup_otps_emailed_not_leaked_in_response(client, monkeypatch):
    monkeypatch.setattr("backend.auth.palmpay_otp_delivery.PALMPAY_DEV_OTP", False)

    sent: list[dict] = []

    def fake_send(*, to, subject, body, timeout_s=12.0):
        sent.append({"to": to, "subject": subject, "body": body})
        return {"sent": True, "provider": "mock"}

    with (
        patch("backend.auth.palmpay_otp_delivery.send_email_detailed", side_effect=fake_send),
        patch("backend.auth.palmpay_otp_delivery.smtp_configured", return_value=True),
    ):
        res = client.post(
            "/api/palmpay/auth/register/signup-start",
            json={
                "full_name": "OTP Tester",
                "email": "otp.tester@example.com",
                "phone": "03001112233",
                "password": "SecurePass1",
            },
        )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("dev_otp_phone") is None
    assert body.get("dev_otp_email") is None
    assert len(sent) == 2
    assert all(m["to"] == "otp.tester@example.com" for m in sent)

    codes = []
    for m in sent:
        codes.extend(re.findall(r"\b(\d{6})\b", m["body"]))
    assert len(codes) >= 2
    phone_otp, email_otp = codes[0], codes[1]

    assert (
        client.post(
            "/api/palmpay/auth/register/verify-phone-signup",
            json={"phone": "03001112233", "otp": phone_otp},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/palmpay/auth/register/verify-email-signup",
            json={"email": "otp.tester@example.com", "otp": email_otp},
        ).status_code
        == 200
    )

    finish = client.post(
        "/api/palmpay/auth/register/finish-signup",
        json={"phone": "03001112233", "email": "otp.tester@example.com", "login_pin": "5829"},
    )
    assert finish.status_code == 200, finish.text

    login = client.post(
        "/api/palmpay/auth/login/email",
        json={"email": "otp.tester@example.com", "password": "SecurePass1"},
    )
    assert login.status_code == 200, login.text
    token = login.json()
    assert token["needs_spending_pin_setup"] is False

    profile = client.get(
        "/api/palmpay/profile",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["spending_pin_set"] is True
    assert profile.json()["needs_spending_pin_setup"] is False


def test_pin_set_writes_spending_pin(client, db, user):
    wallet = user.wallet
    wallet.spending_pin_hash = None
    db.commit()

    res = client.post(
        "/api/palmpay/auth/pin/set",
        headers=auth_header(user),
        json={"login_pin": "5829", "use_same_pin_for_spending": True},
    )
    assert res.status_code == 200, res.text
    assert res.json()["needs_spending_pin_setup"] is False

    db.refresh(wallet)
    assert wallet.spending_pin_hash == hash_spending_pin("5829")
    assert wallet.spending_pin_hash != hash_spending_pin(PALMPAY_DEV_SPENDING_PIN)


def test_forgot_password_sends_email_otp(client, db, monkeypatch):
    monkeypatch.setattr("backend.auth.palmpay_otp_delivery.PALMPAY_DEV_OTP", False)
    seed_account(db, email="reset.otp@example.com", phone="03009998877")

    sent: list[dict] = []

    def fake_send(*, to, subject, body, timeout_s=12.0):
        sent.append({"to": to, "subject": subject, "body": body})
        return {"sent": True}

    with (
        patch("backend.auth.palmpay_otp_delivery.send_email_detailed", side_effect=fake_send),
        patch("backend.auth.palmpay_otp_delivery.smtp_configured", return_value=True),
    ):
        res = client.post(
            "/api/palmpay/auth/password/forgot",
            json={"email": "reset.otp@example.com"},
        )
    assert res.status_code == 200, res.text
    assert res.json().get("dev_otp") is None
    assert len(sent) == 1
    assert "reset" in sent[0]["subject"].lower()
    assert re.search(r"\b\d{6}\b", sent[0]["body"])


def test_profile_flags_missing_spending_pin(client, db, user):
    user.wallet.spending_pin_hash = None
    db.commit()
    res = client.get("/api/palmpay/profile", headers=auth_header(user))
    assert res.status_code == 200
    data = res.json()
    assert data["spending_pin_set"] is False
    assert data["needs_spending_pin_setup"] is True
