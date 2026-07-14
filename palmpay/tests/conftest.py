"""Pytest configuration — isolated SQLite DB for PalmPay tests."""
from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for p in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT / "src" / "xrtech"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Skip heavy recognition / matcher warmup during tests
os.environ.setdefault("RECOGNITION_LOGS_ENABLED", "false")
os.environ.setdefault("PALMPAY_DEV_OTP", "true")

_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db_file.name
_test_db_file.close()

_test_engine = create_engine(
    f"sqlite:///{_test_db_path}",
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(_test_engine, "connect")
def _enable_sqlite_fks(dbapi_conn, _record) -> None:
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


TestSessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False, future=True)


def _patch_db_modules() -> None:
    import backend.db.base as db_base
    import backend.deps as deps

    db_base.engine = _test_engine
    db_base.SessionLocal = TestSessionLocal

    def _get_db() -> Generator[Session, None, None]:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    deps.get_db = _get_db


_patch_db_modules()

from backend.auth.palmpay_phone import normalize_pk_phone
from backend.auth.passwords import hash_password  # noqa: E402
from backend.auth.palmpay_pin import hash_spending_pin  # noqa: E402
from backend.auth.palmpay_tokens import create_palmpay_access_token  # noqa: E402
from backend.db import models  # noqa: E402
from backend.db.base import Base  # noqa: E402
from backend.db.migrate import run_migrations  # noqa: E402
from backend.main import app  # noqa: E402
from backend.settings import PALMPAY_DEV_SPENDING_PIN  # noqa: E402
from backend.wallet.palmpay_wallet_service import get_or_create_wallet  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> None:
    Base.metadata.create_all(bind=_test_engine)
    run_migrations()


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def _clean_tables(db: Session) -> Generator[None, None, None]:
    """Clear PalmPay tables between tests."""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        if table.name.startswith("palmpay_"):
            db.execute(table.delete())
    db.commit()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def seed_account(
    db: Session,
    *,
    email: str = "tester@palmpay.pk",
    phone: str = "03001234567",
    password: str = "Test@Palmpay#1001",
    balance: float = 5000.0,
    frozen: bool = False,
) -> models.PalmPayAccount:
    normalized_phone = normalize_pk_phone(phone)
    if normalized_phone is None:
        raise ValueError(f"Invalid test phone: {phone}")

    account = models.PalmPayAccount(
        phone=normalized_phone,
        email=email,
        password_hash=hash_password(password),
        full_name="Test User",
        kyc_status="verified",
        email_verified=True,
    )
    db.add(account)
    db.flush()
    wallet = get_or_create_wallet(db, account)
    wallet.balance_pkr = balance
    wallet.is_frozen = frozen
    wallet.spending_pin_hash = hash_spending_pin(PALMPAY_DEV_SPENDING_PIN)
    db.commit()
    db.refresh(account)
    return account


def auth_header(account: models.PalmPayAccount) -> dict[str, str]:
    token = create_palmpay_access_token(account.id, account.phone)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user(db: Session) -> models.PalmPayAccount:
    return seed_account(db)


@pytest.fixture()
def auth_client(client: TestClient, user: models.PalmPayAccount) -> TestClient:
    client.headers.update(auth_header(user))
    return client
