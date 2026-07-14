"""ORM models - User, EnrollmentSample, RecognitionLog."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("name", "hand", name="uq_users_name_hand"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    hand: Mapped[str] = mapped_column(String(8), nullable=False)
    template_embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    samples: Mapped[list["EnrollmentSample"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    logs: Mapped[list["RecognitionLog"]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )


class EnrollmentSample(Base):
    __tablename__ = "enrollment_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="samples")


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # "verify"|"identify"
    claimed_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    matched_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="logs")


class Account(Base):
    """Registered platform user (email login + palm biometrics)."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    dataset_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # Roles: admin | employee | customer | shop_owner
    role: Mapped[str] = mapped_column(String(16), default="employee", nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    google_sub: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True, index=True)
    left_template: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    right_template: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    palmpay_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    activities: Mapped[list["ActivityLog"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    shops: Mapped[list["Shop"]] = relationship(
        back_populates="owner",
        foreign_keys="Shop.owner_user_id",
        passive_deletes=True,
    )
    palmpay_account: Mapped[Optional["PalmPayAccount"]] = relationship(
        foreign_keys=[palmpay_account_id],
        uselist=False,
    )


class EmailVerificationCode(Base):
    """One-time email verification code for signup."""

    __tablename__ = "email_verification_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    account: Mapped["Account"] = relationship()


class PasswordResetCode(Base):
    """One-time password reset code."""

    __tablename__ = "password_reset_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    account: Mapped["Account"] = relationship()


class AttendanceRecord(Base):
    """One row per employee per calendar work day."""

    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("account_id", "work_date", name="uq_attendance_account_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="present")
    first_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_logout_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    marked_by: Mapped[str] = mapped_column(String(16), default="system", nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    account: Mapped["Account"] = relationship(back_populates="attendance_records")


class EmployeeInvite(Base):
    """HR-issued signup invite (one-time link)."""

    __tablename__ = "employee_invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    invited_by_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CompanySettings(Base):
    """Singleton company attendance policy (id=1)."""

    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_day_start: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)
    grace_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    require_palm_logout: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    exclude_weekends: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    half_day_hours: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    notify_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_weekly_summary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin_notify_email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class CompanyHoliday(Base):
    """Company-wide non-working day."""

    __tablename__ = "company_holidays"
    __table_args__ = (UniqueConstraint("holiday_date", name="uq_holiday_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    holiday_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class AuthSession(Base):
    """Login session for employee time-on-app tracking."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    login_method: Mapped[str] = mapped_column(String(16), nullable=False)  # email | palm | signup
    logout_method: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    attendance_record_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("attendance_records.id", ondelete="SET NULL"), nullable=True
    )
    login_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)
    logout_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    account: Mapped["Account"] = relationship(back_populates="sessions")


class ActivityLog(Base):
    """Per-employee activity audit trail."""

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    detail: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)

    account: Mapped[Optional["Account"]] = relationship(back_populates="activities")


class TrainingIngestLog(Base):
    """Tracks live captures copied into the training corpus."""

    __tablename__ = "training_ingest_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    dest_path: Mapped[str] = mapped_column(String(512), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    hand: Mapped[str] = mapped_column(String(8), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


class TrainingRun(Base):
    """Weekly / manual model retraining job record."""

    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    trigger: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    images_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    val_eer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    val_rank1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    checkpoint_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PalmPayAccount(Base):
    """PalmPay mobile wallet user (phone + OTP auth)."""

    __tablename__ = "palmpay_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), unique=True, nullable=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    kyc_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    failed_otp_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_pin_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    login_pin_set_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_pin_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    login_locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notif_txn_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notif_security_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notif_promo_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    wallet: Mapped[Optional["PalmPayWallet"]] = relationship(
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    kyc_submissions: Mapped[list["PalmPayKycSubmission"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    palm_templates: Mapped[list["PalmPayPalmTemplate"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    enrollment_sessions: Mapped[list["PalmPayEnrollmentSession"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PalmPayKycSubmission(Base):
    """CNIC + document photos for identity verification."""

    __tablename__ = "palmpay_kyc_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cnic: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    front_image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    back_image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    account: Mapped["PalmPayAccount"] = relationship(back_populates="kyc_submissions")


class PalmPayEnrollmentSession(Base):
    """Kiosk palm enrollment session (QR / short code)."""

    __tablename__ = "palmpay_enrollment_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    account: Mapped["PalmPayAccount"] = relationship(back_populates="enrollment_sessions")


class PalmPayPalmTemplate(Base):
    """Enrolled palm template reference (kiosk capture)."""

    __tablename__ = "palmpay_palm_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hand: Mapped[str] = mapped_column(String(8), default="right", nullable=False)
    template_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    account: Mapped["PalmPayAccount"] = relationship(back_populates="palm_templates")


class PalmPayEmailOtpCode(Base):
    """Email OTP for PalmPay signup."""

    __tablename__ = "palmpay_email_otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


class PalmPaySignupDraft(Base):
    """In-progress signup before account is created."""

    __tablename__ = "palmpay_signup_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class PalmPayOtpCode(Base):
    """SMS OTP challenge (SQLite store — no Redis in standalone dev)."""

    __tablename__ = "palmpay_otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


class PalmPayWallet(Base):
    """Wallet balance for a PalmPay account."""

    __tablename__ = "palmpay_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    balance_pkr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    spending_pin_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    per_txn_limit_pkr: Mapped[float] = mapped_column(Float, default=500_000.0, nullable=False)
    palm_pay_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    account: Mapped["PalmPayAccount"] = relationship(back_populates="wallet")
    ledger_entries: Mapped[list["PalmPayLedgerEntry"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PalmPayRefreshToken(Base):
    """Long-lived refresh token (hashed at rest)."""

    __tablename__ = "palmpay_refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class PalmPayTransaction(Base):
    """Wallet movement record (transfer, top-up, palm pay)."""

    __tablename__ = "palmpay_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    tx_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    from_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    to_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="complete", nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    topup_method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    topup_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    merchant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_merchants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_payment_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    ledger_entries: Mapped[list["PalmPayLedgerEntry"]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PalmPayLedgerEntry(Base):
    """Double-entry ledger line for every balance change."""

    __tablename__ = "palmpay_ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_type: Mapped[str] = mapped_column(String(8), nullable=False)
    amount_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)

    transaction: Mapped["PalmPayTransaction"] = relationship(back_populates="ledger_entries")
    wallet: Mapped["PalmPayWallet"] = relationship(back_populates="ledger_entries")


class PalmPayTransferDraft(Base):
    """Pending P2P transfer awaiting spending PIN confirmation."""

    __tablename__ = "palmpay_transfer_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    sender_account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class PalmPayTopUpOrder(Base):
    """Top-up checkout (JazzCash / dev simulate)."""

    __tablename__ = "palmpay_topup_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(32), default="jazzcash", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    external_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PalmPayMerchant(Base):
    """Merchant terminal that receives palm payments."""

    __tablename__ = "palmpay_merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="retail", nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class PalmPayPaymentRequest(Base):
    """Open payment at a kiosk — expires after TTL."""

    __tablename__ = "palmpay_payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kiosk_id: Mapped[str] = mapped_column(String(64), default="kiosk-dev", nullable=False)
    amount_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    payer_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)

    merchant: Mapped["PalmPayMerchant"] = relationship(
        foreign_keys=[merchant_id],
        lazy="joined",
    )


class PalmPayUserNotification(Base):
    """In-app notification (FCM stub for dev)."""

    __tablename__ = "palmpay_user_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("palmpay_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    body: Mapped[str] = mapped_column(String(512), nullable=False)
    payload_json: Mapped[str] = mapped_column(String(2048), default="{}", nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


class Shop(Base):
    """Merchant shop listing products on the VeinPay marketplace."""

    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    approved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    wallet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_wallets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    owner: Mapped["Account"] = relationship(
        back_populates="shops",
        foreign_keys=[owner_user_id],
    )
    products: Mapped[list["Product"]] = relationship(
        back_populates="shop",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Product(Base):
    """Product listed by a shop for palm-vein checkout."""

    __tablename__ = "products"
    __table_args__ = (CheckConstraint("stock_qty >= 0", name="ck_products_stock_nonneg"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    price_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    images: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="products")


class Cart(Base):
    """Shopping cart — either user-owned or anonymous session cart."""

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True, unique=True, index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CartItem(Base):
    """Line item in a cart with price snapshot at add time."""

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        CheckConstraint("quantity >= 1", name="ck_cart_items_qty_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price_at_add: Mapped[float] = mapped_column(Float, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class ShopOrder(Base):
    """Marketplace order paid via palm vein + VeinPay wallet."""

    __tablename__ = "shop_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    # pending/confirmed/cancelled/expired
    subtotal_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee_pkr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_pkr: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), default="palm_vein", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    # pending/paid/failed/refunded
    transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("palmpay_transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    palm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scan_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    items: Mapped[list["ShopOrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ShopOrderItem(Base):
    """Line item on a shop order (supports multi-shop carts)."""

    __tablename__ = "shop_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    shop_id: Mapped[int] = mapped_column(
        ForeignKey("shops.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    line_total: Mapped[float] = mapped_column(Float, nullable=False)
    shop_earnings: Mapped[float] = mapped_column(Float, nullable=False)
    platform_take: Mapped[float] = mapped_column(Float, nullable=False)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)

    order: Mapped["ShopOrder"] = relationship(back_populates="items")
