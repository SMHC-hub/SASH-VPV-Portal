"""Lightweight SQLite migrations run on startup."""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from backend.db.base import engine

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    _migrate_users_name_hand_unique()
    _migrate_account_role()
    _ensure_admin_role()
    _migrate_auth_session_columns()
    _ensure_phase1_tables()
    _ensure_phase3_columns()
    _ensure_phase3_tables()
    _ensure_google_sub_column()
    _ensure_customer_auth_columns()
    _ensure_email_verification_table()
    _ensure_training_tables()
    _ensure_password_reset_table()
    _ensure_palmpay_tables()
    _ensure_palmpay_day3_tables()
    _ensure_palmpay_day4_tables()
    _ensure_palmpay_day5_tables()
    _ensure_palmpay_day11_auth()
    _ensure_palmpay_day12_email_auth()
    _ensure_palmpay_day7_profile_security()
    _ensure_palmpay_day8_indexes()
    _ensure_shop_tables()
    _ensure_account_palmpay_link()
    _ensure_shop_moderation_columns()
    _ensure_cart_tables()
    _ensure_shop_order_tables()


def _ensure_training_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {"training_ingest_log", "training_runs"}
    missing = needed - existing
    if not missing:
        return
    logger.info("Creating training tables: %s", missing)
    Base.metadata.create_all(
        bind=engine,
        tables=[models.TrainingIngestLog.__table__, models.TrainingRun.__table__],
    )


def _ensure_password_reset_table() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    if "password_reset_codes" in insp.get_table_names():
        return
    logger.info("Creating password_reset_codes table")
    Base.metadata.create_all(bind=engine, tables=[models.PasswordResetCode.__table__])


def _migrate_account_role() -> None:
    insp = inspect(engine)
    if "accounts" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("accounts")}
    if "role" in cols:
        return
    logger.info("Adding accounts.role column")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE accounts ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'employee'"))
        conn.commit()


def _ensure_admin_role() -> None:
    """Bootstrap: ensure at least one admin exists; never re-promote the first account if an admin is already set."""
    preferred_admin = "saudakbar65367@gmail.com"
    with engine.connect() as conn:
        admin_count = conn.execute(
            text("SELECT COUNT(*) FROM accounts WHERE role = 'admin'")
        ).scalar_one()
        if admin_count:
            return
        row = conn.execute(
            text("SELECT id FROM accounts WHERE lower(email) = lower(:email)"),
            {"email": preferred_admin},
        ).fetchone()
        if not row:
            row = conn.execute(text("SELECT id FROM accounts ORDER BY id LIMIT 1")).fetchone()
        if row:
            conn.execute(
                text("UPDATE accounts SET role = 'admin' WHERE id = :id"),
                {"id": row[0]},
            )
            conn.commit()


def _migrate_users_name_hand_unique() -> None:
    """Allow the same dataset name for Left and Right (unique on name+hand)."""
    insp = inspect(engine)
    tables = insp.get_table_names()
    if "users" not in tables:
        return

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        ).fetchone()
        if not row or not row[0]:
            return
        create_sql = row[0]
        if "UNIQUE (name, hand)" in create_sql or "UNIQUE(name, hand)" in create_sql:
            return

        logger.info("Migrating users table: unique(name) -> unique(name, hand)")
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(
            text(
                "CREATE TABLE users_new ("
                "id INTEGER NOT NULL PRIMARY KEY, "
                "name VARCHAR(128) NOT NULL, "
                "hand VARCHAR(8) NOT NULL, "
                "template_embedding BLOB NOT NULL, "
                "created_at DATETIME NOT NULL, "
                "CONSTRAINT uq_users_name_hand UNIQUE (name, hand))"
            )
        )
        conn.execute(
            text(
                "INSERT INTO users_new (id, name, hand, template_embedding, created_at) "
                "SELECT id, name, hand, template_embedding, created_at FROM users"
            )
        )
        conn.execute(text("DROP TABLE users"))
        conn.execute(text("ALTER TABLE users_new RENAME TO users"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_name ON users (name)"))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()
        logger.info("users table migration complete")


def _migrate_auth_session_columns() -> None:
    insp = inspect(engine)
    if "auth_sessions" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("auth_sessions")}
    with engine.connect() as conn:
        if "logout_method" not in cols:
            logger.info("Adding auth_sessions.logout_method")
            conn.execute(text("ALTER TABLE auth_sessions ADD COLUMN logout_method VARCHAR(16)"))
        if "attendance_record_id" not in cols:
            logger.info("Adding auth_sessions.attendance_record_id")
            conn.execute(text("ALTER TABLE auth_sessions ADD COLUMN attendance_record_id INTEGER"))
        conn.commit()


def _ensure_phase1_tables() -> None:
    """Create attendance, invites, settings tables via SQLAlchemy metadata if missing."""
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {"attendance_records", "employee_invites", "company_settings"}
    if needed.issubset(existing):
        return
    logger.info("Creating phase-1 tables: %s", needed - existing)
    Base.metadata.create_all(bind=engine, tables=[
        models.AttendanceRecord.__table__,
        models.EmployeeInvite.__table__,
        models.CompanySettings.__table__,
    ])
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM company_settings WHERE id = 1")).fetchone()
        if not row:
            conn.execute(
                text(
                    "INSERT INTO company_settings (id, work_day_start, grace_minutes, timezone, require_palm_logout) "
                    "VALUES (1, '09:00', 30, 'UTC', 1)"
                )
            )
            conn.commit()
            logger.info("Seeded default company_settings (grace=30min)")


def _ensure_phase3_columns() -> None:
    insp = inspect(engine)
    if "company_settings" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("company_settings")}
    additions = [
        ("exclude_weekends", "BOOLEAN NOT NULL DEFAULT 1"),
        ("half_day_hours", "FLOAT NOT NULL DEFAULT 4.0"),
        ("notify_absent", "BOOLEAN NOT NULL DEFAULT 0"),
        ("notify_weekly_summary", "BOOLEAN NOT NULL DEFAULT 0"),
        ("admin_notify_email", "VARCHAR(256)"),
    ]
    with engine.connect() as conn:
        for name, sql_type in additions:
            if name not in cols:
                logger.info("Adding company_settings.%s", name)
                conn.execute(text(f"ALTER TABLE company_settings ADD COLUMN {name} {sql_type}"))
        conn.commit()


def _ensure_phase3_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    if "company_holidays" in insp.get_table_names():
        return
    logger.info("Creating company_holidays table")
    Base.metadata.create_all(bind=engine, tables=[models.CompanyHoliday.__table__])


def _ensure_google_sub_column() -> None:
    insp = inspect(engine)
    if "accounts" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("accounts")}
    if "google_sub" in cols:
        return
    logger.info("Adding accounts.google_sub column")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE accounts ADD COLUMN google_sub VARCHAR(128)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_google_sub ON accounts (google_sub)"))
        conn.commit()


def _ensure_customer_auth_columns() -> None:
    insp = inspect(engine)
    if "accounts" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("accounts")}
    with engine.connect() as conn:
        if "username" not in cols:
            logger.info("Adding accounts.username column")
            conn.execute(text("ALTER TABLE accounts ADD COLUMN username VARCHAR(64)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_username ON accounts (username)"))
        if "email_verified" not in cols:
            logger.info("Adding accounts.email_verified column")
            conn.execute(text("ALTER TABLE accounts ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0"))
            conn.execute(text("UPDATE accounts SET email_verified = 1 WHERE role != 'customer'"))
        conn.commit()


def _ensure_email_verification_table() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    if "email_verification_codes" in insp.get_table_names():
        return
    logger.info("Creating email_verification_codes table")
    Base.metadata.create_all(bind=engine, tables=[models.EmailVerificationCode.__table__])


def _ensure_palmpay_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {
        "palmpay_accounts",
        "palmpay_otp_codes",
        "palmpay_wallets",
        "palmpay_refresh_tokens",
    }
    missing = needed - existing
    if not missing:
        return
    logger.info("Creating PalmPay tables: %s", missing)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            models.PalmPayAccount.__table__,
            models.PalmPayOtpCode.__table__,
            models.PalmPayWallet.__table__,
            models.PalmPayRefreshToken.__table__,
        ],
    )


def _ensure_palmpay_day3_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {
        "palmpay_kyc_submissions",
        "palmpay_enrollment_sessions",
        "palmpay_palm_templates",
    }
    missing = needed - existing
    if not missing:
        return
    logger.info("Creating PalmPay Day-3 tables: %s", missing)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            models.PalmPayKycSubmission.__table__,
            models.PalmPayEnrollmentSession.__table__,
            models.PalmPayPalmTemplate.__table__,
        ],
    )


def _ensure_palmpay_day4_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {
        "palmpay_transactions",
        "palmpay_ledger_entries",
        "palmpay_transfer_drafts",
        "palmpay_topup_orders",
    }
    missing = needed - existing
    if missing:
        logger.info("Creating PalmPay Day-4 tables: %s", missing)
        Base.metadata.create_all(
            bind=engine,
            tables=[
                models.PalmPayTransaction.__table__,
                models.PalmPayLedgerEntry.__table__,
                models.PalmPayTransferDraft.__table__,
                models.PalmPayTopUpOrder.__table__,
            ],
        )

    wallet_cols = {c["name"] for c in insp.get_columns("palmpay_wallets")}
    alters: list[str] = []
    if "spending_pin_hash" not in wallet_cols:
        alters.append("ALTER TABLE palmpay_wallets ADD COLUMN spending_pin_hash VARCHAR(64)")
    if "is_frozen" not in wallet_cols:
        alters.append("ALTER TABLE palmpay_wallets ADD COLUMN is_frozen BOOLEAN NOT NULL DEFAULT 0")
    if "per_txn_limit_pkr" not in wallet_cols:
        alters.append(
            "ALTER TABLE palmpay_wallets ADD COLUMN per_txn_limit_pkr FLOAT NOT NULL DEFAULT 500000"
        )
    if "palm_pay_enabled" not in wallet_cols:
        alters.append(
            "ALTER TABLE palmpay_wallets ADD COLUMN palm_pay_enabled BOOLEAN NOT NULL DEFAULT 1"
        )
    if alters:
        logger.info("Adding PalmPay wallet columns: %s", [a.split()[3] for a in alters])
        with engine.begin() as conn:
            for stmt in alters:
                conn.execute(text(stmt))

    from backend.auth.palmpay_pin import hash_spending_pin
    from backend.settings import PALMPAY_DEV_OTP, PALMPAY_DEV_SPENDING_PIN

    # Never force the demo PIN onto production wallets.
    if PALMPAY_DEV_OTP:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE palmpay_wallets SET spending_pin_hash = :hash "
                    "WHERE spending_pin_hash IS NULL"
                ),
                {"hash": hash_spending_pin(PALMPAY_DEV_SPENDING_PIN)},
            )


def _ensure_palmpay_day5_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {
        "palmpay_merchants",
        "palmpay_payment_requests",
        "palmpay_user_notifications",
    }
    missing = needed - existing
    if missing:
        logger.info("Creating PalmPay Day-5 tables: %s", missing)
        Base.metadata.create_all(
            bind=engine,
            tables=[
                models.PalmPayMerchant.__table__,
                models.PalmPayPaymentRequest.__table__,
                models.PalmPayUserNotification.__table__,
            ],
        )

    if "palmpay_transactions" in existing:
        tx_cols = {c["name"] for c in insp.get_columns("palmpay_transactions")}
        alters: list[str] = []
        if "merchant_id" not in tx_cols:
            alters.append(
                "ALTER TABLE palmpay_transactions ADD COLUMN merchant_id INTEGER "
                "REFERENCES palmpay_merchants(id) ON DELETE SET NULL"
            )
        if "payment_request_id" not in tx_cols:
            alters.append(
                "ALTER TABLE palmpay_transactions ADD COLUMN payment_request_id INTEGER "
                "REFERENCES palmpay_payment_requests(id) ON DELETE SET NULL"
            )
        if "idempotency_key" not in tx_cols:
            alters.append(
                "ALTER TABLE palmpay_transactions ADD COLUMN idempotency_key VARCHAR(64)"
            )
        if alters:
            logger.info("Adding PalmPay transaction columns for palm pay")
            with engine.begin() as conn:
                for stmt in alters:
                    conn.execute(text(stmt))

    from backend.db.base import SessionLocal
    from backend.wallet.palmpay_payment_service import ensure_dev_merchant

    db = SessionLocal()
    try:
        ensure_dev_merchant(db)
    finally:
        db.close()


def _ensure_palmpay_day11_auth() -> None:
    insp = inspect(engine)
    if "palmpay_accounts" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("palmpay_accounts")}
    alters: list[str] = []
    if "login_pin_hash" not in cols:
        alters.append("ALTER TABLE palmpay_accounts ADD COLUMN login_pin_hash VARCHAR(64)")
    if "login_pin_set_at" not in cols:
        alters.append("ALTER TABLE palmpay_accounts ADD COLUMN login_pin_set_at DATETIME")
    if "failed_login_pin_attempts" not in cols:
        alters.append(
            "ALTER TABLE palmpay_accounts ADD COLUMN failed_login_pin_attempts INTEGER NOT NULL DEFAULT 0"
        )
    if "login_locked_until" not in cols:
        alters.append("ALTER TABLE palmpay_accounts ADD COLUMN login_locked_until DATETIME")

    if alters:
        logger.info("Adding PalmPay Day-11 login PIN columns")
        with engine.begin() as conn:
            for stmt in alters:
                conn.execute(text(stmt))


def _ensure_palmpay_day12_email_auth() -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    if "palmpay_accounts" in tables:
        cols = {c["name"] for c in insp.get_columns("palmpay_accounts")}
        alters: list[str] = []
        if "email" not in cols:
            alters.append("ALTER TABLE palmpay_accounts ADD COLUMN email VARCHAR(256)")
        if "password_hash" not in cols:
            alters.append("ALTER TABLE palmpay_accounts ADD COLUMN password_hash VARCHAR(256)")
        if "email_verified" not in cols:
            alters.append(
                "ALTER TABLE palmpay_accounts ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0"
            )
        if "phone_verified" not in cols:
            alters.append(
                "ALTER TABLE palmpay_accounts ADD COLUMN phone_verified BOOLEAN NOT NULL DEFAULT 0"
            )
        if alters:
            logger.info("Adding PalmPay Day-12 email auth columns")
            with engine.begin() as conn:
                for stmt in alters:
                    conn.execute(text(stmt))

    if "palmpay_email_otp_codes" not in tables:
        logger.info("Creating palmpay_email_otp_codes table")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE palmpay_email_otp_codes (
                        id INTEGER PRIMARY KEY,
                        email VARCHAR(256) NOT NULL,
                        code VARCHAR(6) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        used_at DATETIME,
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX ix_palmpay_email_otp_codes_email ON palmpay_email_otp_codes (email)")
            )

    if "palmpay_signup_drafts" not in tables:
        logger.info("Creating palmpay_signup_drafts table")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE palmpay_signup_drafts (
                        id INTEGER PRIMARY KEY,
                        phone VARCHAR(16) NOT NULL UNIQUE,
                        email VARCHAR(256) NOT NULL UNIQUE,
                        full_name VARCHAR(128) NOT NULL,
                        password_hash VARCHAR(256) NOT NULL,
                        phone_verified BOOLEAN NOT NULL DEFAULT 0,
                        email_verified BOOLEAN NOT NULL DEFAULT 0,
                        expires_at DATETIME NOT NULL,
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )


def _ensure_palmpay_day7_profile_security() -> None:
    insp = inspect(engine)
    if "palmpay_accounts" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("palmpay_accounts")}
    alters: list[str] = []
    if "notif_txn_enabled" not in cols:
        alters.append(
            "ALTER TABLE palmpay_accounts ADD COLUMN notif_txn_enabled BOOLEAN NOT NULL DEFAULT 1"
        )
    if "notif_security_enabled" not in cols:
        alters.append(
            "ALTER TABLE palmpay_accounts ADD COLUMN notif_security_enabled BOOLEAN NOT NULL DEFAULT 1"
        )
    if "notif_promo_enabled" not in cols:
        alters.append(
            "ALTER TABLE palmpay_accounts ADD COLUMN notif_promo_enabled BOOLEAN NOT NULL DEFAULT 0"
        )
    if alters:
        logger.info("Adding PalmPay Day-7 profile/security columns")
        with engine.begin() as conn:
            for stmt in alters:
                conn.execute(text(stmt))


def _ensure_palmpay_day8_indexes() -> None:
    """Composite indexes for transaction history and ledger queries (Day 8)."""
    insp = inspect(engine)
    if "palmpay_transactions" not in insp.get_table_names():
        return

    indexes = [
        (
            "idx_pp_tx_from_created",
            "CREATE INDEX IF NOT EXISTS idx_pp_tx_from_created "
            "ON palmpay_transactions (from_account_id, created_at)",
        ),
        (
            "idx_pp_tx_to_created",
            "CREATE INDEX IF NOT EXISTS idx_pp_tx_to_created "
            "ON palmpay_transactions (to_account_id, created_at)",
        ),
        (
            "idx_pp_tx_status_created",
            "CREATE INDEX IF NOT EXISTS idx_pp_tx_status_created "
            "ON palmpay_transactions (status, created_at)",
        ),
        (
            "idx_pp_ledger_wallet_created",
            "CREATE INDEX IF NOT EXISTS idx_pp_ledger_wallet_created "
            "ON palmpay_ledger_entries (wallet_id, created_at)",
        ),
    ]

    existing: set[str] = set()
    for table in ("palmpay_transactions", "palmpay_ledger_entries"):
        if table in insp.get_table_names():
            existing |= {idx["name"] for idx in insp.get_indexes(table)}

    pending = [(name, sql) for name, sql in indexes if name not in existing]
    if not pending:
        return

    logger.info("Creating PalmPay Day-8 indexes: %s", [n for n, _ in pending])
    with engine.begin() as conn:
        for _, sql in pending:
            conn.execute(text(sql))


def _ensure_shop_tables() -> None:
    """VeinPay marketplace: shops + products (+ demo seed)."""
    from backend.db.base import Base, SessionLocal
    from backend.db import models  # noqa: F401
    from backend.shop.seed_demo import ensure_demo_shop

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {"shops", "products"}
    missing = needed - existing
    if missing:
        logger.info("Creating shop marketplace tables: %s", missing)
        Base.metadata.create_all(
            bind=engine,
            tables=[models.Shop.__table__, models.Product.__table__],
        )

    # Columns may be missing on DBs created before moderation fields existed
    _ensure_shop_moderation_columns()

    db = SessionLocal()
    try:
        ensure_demo_shop(db)
    finally:
        db.close()

def _ensure_account_palmpay_link() -> None:
    """Link web accounts.palmpay_account_id → palmpay_accounts (email match + demo owner)."""
    insp = inspect(engine)
    if "accounts" not in insp.get_table_names():
        return
    if "palmpay_accounts" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("accounts")}
    if "palmpay_account_id" not in cols:
        logger.info("Adding accounts.palmpay_account_id column")
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE accounts ADD COLUMN palmpay_account_id INTEGER "
                    "REFERENCES palmpay_accounts(id) ON DELETE SET NULL"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_palmpay_account_id "
                    "ON accounts (palmpay_account_id)"
                )
            )

    from backend.db.base import SessionLocal
    from backend.shop.identity_link import backfill_links_by_email
    from backend.shop.seed_demo import ensure_demo_shop_wallet_link

    db = SessionLocal()
    try:
        n = backfill_links_by_email(db)
        if n:
            logger.info("Backfilled %s Account↔PalmPay links by email", n)
        ensure_demo_shop_wallet_link(db)
    finally:
        db.close()


def _ensure_shop_moderation_columns() -> None:
    """rejection_reason on shops/products for admin reject flow."""
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    alters: list[str] = []
    if "shops" in tables:
        cols = {c["name"] for c in insp.get_columns("shops")}
        if "rejection_reason" not in cols:
            alters.append("ALTER TABLE shops ADD COLUMN rejection_reason VARCHAR(500)")
    if "products" in tables:
        cols = {c["name"] for c in insp.get_columns("products")}
        if "rejection_reason" not in cols:
            alters.append("ALTER TABLE products ADD COLUMN rejection_reason VARCHAR(500)")
    if not alters:
        return
    logger.info("Adding shop moderation columns")
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))


def _ensure_cart_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {"carts", "cart_items"}
    missing = needed - existing
    if not missing:
        return
    logger.info("Creating cart tables: %s", missing)
    Base.metadata.create_all(
        bind=engine,
        tables=[models.Cart.__table__, models.CartItem.__table__],
    )


def _ensure_shop_order_tables() -> None:
    from backend.db.base import Base
    from backend.db import models  # noqa: F401

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    needed = {"shop_orders", "shop_order_items"}
    missing = needed - existing
    if not missing:
        return
    logger.info("Creating shop order tables: %s", missing)
    Base.metadata.create_all(
        bind=engine,
        tables=[models.ShopOrder.__table__, models.ShopOrderItem.__table__],
    )
