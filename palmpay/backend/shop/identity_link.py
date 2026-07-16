"""Link web Account ↔ PalmPayAccount / wallet (shared identity for shop checkout)."""
from __future__ import annotations

import logging
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db import models
from backend.wallet.palmpay_wallet_service import get_or_create_wallet

logger = logging.getLogger(__name__)

# Reserved demo phone for marketplace shop-owner wallet (not a real MSISDN)
DEMO_SHOP_OWNER_PHONE = "03988888888"


def _norm_email(email: str | None) -> str | None:
    if not email:
        return None
    e = email.strip().lower()
    return e or None


def get_linked_palmpay_account(
    db: Session, account: models.Account
) -> models.PalmPayAccount | None:
    """Return the PalmPay account linked to a web Account, if any."""
    if account.palmpay_account_id:
        pp = db.get(models.PalmPayAccount, account.palmpay_account_id)
        if pp is not None:
            return pp
    return resolve_palmpay_by_email(db, account.email)


def resolve_palmpay_by_email(db: Session, email: str | None) -> models.PalmPayAccount | None:
    email_l = _norm_email(email)
    if not email_l:
        return None
    return db.execute(
        select(models.PalmPayAccount).where(func.lower(models.PalmPayAccount.email) == email_l)
    ).scalar_one_or_none()


def link_account_to_palmpay(
    db: Session,
    account: models.Account,
    palmpay_account: models.PalmPayAccount,
    *,
    commit: bool = False,
) -> models.PalmPayAccount:
    """Persist FK link. Raises ValueError on conflict with another web account."""
    other = db.execute(
        select(models.Account).where(
            models.Account.palmpay_account_id == palmpay_account.id,
            models.Account.id != account.id,
        )
    ).scalar_one_or_none()
    if other is not None:
        raise ValueError(
            f"PalmPay account {palmpay_account.id} already linked to web account {other.id}"
        )

    if (
        account.palmpay_account_id is not None
        and account.palmpay_account_id != palmpay_account.id
    ):
        raise ValueError(
            f"Web account {account.id} already linked to PalmPay {account.palmpay_account_id}"
        )

    account.palmpay_account_id = palmpay_account.id

    # Keep emails aligned when PalmPay email was empty
    email_l = _norm_email(account.email)
    if email_l and not palmpay_account.email:
        conflict = db.execute(
            select(models.PalmPayAccount).where(
                func.lower(models.PalmPayAccount.email) == email_l,
                models.PalmPayAccount.id != palmpay_account.id,
            )
        ).scalar_one_or_none()
        if conflict is None:
            palmpay_account.email = email_l

    if commit:
        db.commit()
        db.refresh(account)
    return palmpay_account


def resolve_or_link_palmpay_by_email(
    db: Session, account: models.Account, *, commit: bool = False
) -> models.PalmPayAccount | None:
    """If FK missing, link by matching email. Returns linked PalmPay account or None."""
    if account.palmpay_account_id:
        pp = db.get(models.PalmPayAccount, account.palmpay_account_id)
        if pp is not None:
            return pp

    pp = resolve_palmpay_by_email(db, account.email)
    if pp is None:
        return None
    return link_account_to_palmpay(db, account, pp, commit=commit)


def get_linked_wallet(
    db: Session, account: models.Account, *, auto_link: bool = True
) -> models.PalmPayWallet | None:
    """
    Wallet for a web Account (shop checkout / earnings).
    Does not create a PalmPay account — only resolves an existing link.
    """
    if auto_link:
        pp = resolve_or_link_palmpay_by_email(db, account, commit=False)
    else:
        pp = get_linked_palmpay_account(db, account)
    if pp is None:
        return None
    return get_or_create_wallet(db, pp)


def ensure_palmpay_link_for_account(
    db: Session,
    account: models.Account,
    *,
    phone: str | None = None,
    commit: bool = False,
) -> tuple[models.PalmPayAccount, models.PalmPayWallet]:
    """
    Ensure web Account has a PalmPay account + wallet.
    Creates PalmPay row when none exists (dev / shop-owner bootstrap).
    """
    pp = resolve_or_link_palmpay_by_email(db, account, commit=False)
    if pp is None:
        email_l = _norm_email(account.email)
        if not phone:
            # Synthetic unique phone reserved for auto-provisioned wallets
            phone = f"038{account.id:08d}"[-11:] if account.id else f"038{secrets.token_hex(4)}"
        existing_phone = db.execute(
            select(models.PalmPayAccount).where(models.PalmPayAccount.phone == phone)
        ).scalar_one_or_none()
        if existing_phone is not None:
            phone = f"037{secrets.token_hex(4)}"

        pp = models.PalmPayAccount(
            phone=phone,
            email=email_l,
            password_hash=account.password_hash,
            email_verified=bool(account.email_verified),
            phone_verified=False,
            full_name=(account.full_name or "")[:128],
            kyc_status="pending",
        )
        db.add(pp)
        db.flush()
        link_account_to_palmpay(db, account, pp, commit=False)
        logger.info(
            "Provisioned PalmPay account id=%s for web account id=%s email=%s",
            pp.id,
            account.id,
            email_l,
        )

    wallet = get_or_create_wallet(db, pp)
    if commit:
        db.commit()
        db.refresh(account)
        db.refresh(pp)
        db.refresh(wallet)
    return pp, wallet


def backfill_links_by_email(db: Session) -> int:
    """Link all web accounts whose email matches a PalmPay email. Returns link count."""
    linked = 0
    accounts = db.execute(
        select(models.Account).where(models.Account.palmpay_account_id.is_(None))
    ).scalars().all()
    for acc in accounts:
        pp = resolve_palmpay_by_email(db, acc.email)
        if pp is None:
            continue
        try:
            link_account_to_palmpay(db, acc, pp, commit=False)
            linked += 1
        except ValueError as exc:
            logger.warning("Skip link account_id=%s: %s", acc.id, exc)
    if linked:
        db.commit()
    return linked


def link_web_accounts_matching_palmpay(
    db: Session, palmpay_account: models.PalmPayAccount, *, commit: bool = False
) -> models.Account | None:
    """If a web Account shares this PalmPay email, link it (1:1)."""
    email_l = _norm_email(palmpay_account.email)
    if not email_l:
        return None
    web = db.execute(
        select(models.Account).where(func.lower(models.Account.email) == email_l)
    ).scalar_one_or_none()
    if web is None:
        return None
    try:
        link_account_to_palmpay(db, web, palmpay_account, commit=commit)
    except ValueError as exc:
        logger.warning("Skip reverse link palmpay_id=%s: %s", palmpay_account.id, exc)
        return None
    return web


def ensure_web_account_for_palmpay(
    db: Session,
    palmpay_account: models.PalmPayAccount,
    *,
    commit: bool = False,
) -> models.Account:
    """
    Ensure a web Account exists for a PalmPay user (for NIR kiosk enrollment).
    Reuses email match when possible; otherwise provisions a customer Account.
    """
    from backend.auth.folder_mapping import next_folder_id
    from backend.auth.passwords import hash_password

    existing = db.execute(
        select(models.Account).where(models.Account.palmpay_account_id == palmpay_account.id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    linked = link_web_accounts_matching_palmpay(db, palmpay_account, commit=False)
    if linked is not None:
        if commit:
            db.commit()
            db.refresh(linked)
        return linked

    email_l = _norm_email(palmpay_account.email)
    if not email_l:
        email_l = f"pp{palmpay_account.id}@veinpay.mobile"

    clash = db.execute(
        select(models.Account).where(func.lower(models.Account.email) == email_l)
    ).scalar_one_or_none()
    if clash is not None:
        try:
            link_account_to_palmpay(db, clash, palmpay_account, commit=False)
        except ValueError:
            email_l = f"pp{palmpay_account.id}.{secrets.token_hex(3)}@veinpay.mobile"
        else:
            if commit:
                db.commit()
                db.refresh(clash)
            return clash

    full_name = (palmpay_account.full_name or "").strip() or f"PalmPay User {palmpay_account.id}"
    base_dataset = "".join(c if c.isalnum() or c in " -_" else "" for c in full_name).strip()
    if not base_dataset:
        base_dataset = f"PalmPay{palmpay_account.id}"
    dataset_name = base_dataset[:120]
    # Ensure unique dataset_name
    n = 0
    while (
        db.execute(
            select(models.Account.id).where(models.Account.dataset_name == dataset_name)
        ).scalar_one_or_none()
        is not None
    ):
        n += 1
        dataset_name = f"{base_dataset[:100]}_{n}"

    folder_id = next_folder_id(db)
    pwd = palmpay_account.password_hash or hash_password(secrets.token_urlsafe(24))

    account = models.Account(
        email=email_l,
        password_hash=pwd,
        full_name=full_name[:256],
        dataset_id=folder_id,
        dataset_name=dataset_name,
        role="customer",
        email_verified=bool(palmpay_account.email_verified or palmpay_account.email),
        palmpay_account_id=palmpay_account.id,
    )
    db.add(account)
    db.flush()
    logger.info(
        "Provisioned web Account id=%s for PalmPay id=%s email=%s",
        account.id,
        palmpay_account.id,
        email_l,
    )
    if commit:
        db.commit()
        db.refresh(account)
    return account

