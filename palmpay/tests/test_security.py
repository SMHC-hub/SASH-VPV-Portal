"""Security tests — rate limits, injection, token hardening."""
from __future__ import annotations

import base64
import json

from backend.auth.jwt_tokens import create_access_token, decode_access_token
from backend.auth.palmpay_tokens import create_palmpay_access_token, decode_palmpay_access_token
from backend.utils.rate_limit import _hits, _lock, check_rate_limit


def test_palmpay_token_rejects_forged_signature(user):
    token = create_palmpay_access_token(user.id, user.phone)
    body, _sig = token.rsplit(".", 1)
    forged = f"{body}.forgedsig"
    assert decode_palmpay_access_token(forged) is None


def test_palmpay_token_rejects_alg_none_style_payload(user):
    """Custom tokens have no alg header; tampered payload must fail."""
    token = create_palmpay_access_token(user.id, user.phone)
    body, sig = token.rsplit(".", 1)
    pad = "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(body + pad))
    payload["sub"] = 999999
    tampered_body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    assert decode_palmpay_access_token(f"{tampered_body}.{sig}") is None


def test_sash_access_token_roundtrip():
    token = create_access_token(1, "admin@test.pk")
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == 1
    assert decoded["email"] == "admin@test.pk"


def test_rate_limit_blocks_sensitive_endpoint():
    with _lock:
        _hits.clear()

    path = "/api/palmpay/auth/password/forgot"
    allowed = 0
    blocked = 0
    for _ in range(30):
        ok, retry = check_rate_limit("10.0.0.1", path)
        if ok:
            allowed += 1
        else:
            blocked += 1
            assert retry >= 1

    assert allowed <= 20
    assert blocked >= 10


def test_sql_injection_in_transaction_search_does_not_crash(auth_client, db):
    from tests.conftest import seed_account

    seed_account(db, email="inj@palmpay.pk", phone="03005555555")
    client = auth_client

    res = client.get(
        "/api/palmpay/transactions",
        params={"search": "'; DROP TABLE palmpay_accounts;--"},
    )
    assert res.status_code == 200
    assert isinstance(res.json().get("items"), list)

    health = client.get("/api/palmpay/health")
    assert health.status_code == 200
    assert health.json()["database_ok"] is True


def test_health_reports_cache_and_redis_flags(client):
    res = client.get("/api/palmpay/health")
    assert res.status_code == 200
    body = res.json()
    assert body["redis_available"] is False
    assert body["wallet_cache_enabled"] is True
