"""PalmPay Google Sign-In — same Google identity as the web member portal."""
from __future__ import annotations

import logging
import re
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth.google_oauth import verify_google_credential
from backend.auth.passwords import hash_password
from backend.auth.registration import persist_customer_account, username_taken
from backend.db import models
from backend.deps import get_db
from backend.settings import GOOGLE_CLIENT_ID
from backend.shop.identity_link import (
    ensure_palmpay_link_for_account,
    ensure_web_account_for_palmpay,
    link_web_accounts_matching_palmpay,
    resolve_palmpay_by_email,
)
from backend.wallet.palmpay_wallet_service import get_or_create_wallet

logger = logging.getLogger(__name__)


class GoogleConfigResponse(BaseModel):
    enabled: bool
    client_id: str | None = None


class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=20)
    intent: Literal["login", "signup"] = "login"


def register_google_auth_routes(router: APIRouter, helpers: dict) -> None:
    issue_token_pair = helpers["issue_token_pair"]
    token_response = helpers["build_token_response"]
    TokenResponse = helpers["TokenResponse"]

    @router.get("/google/config", response_model=GoogleConfigResponse)
    def google_config() -> GoogleConfigResponse:
        return GoogleConfigResponse(
            enabled=bool(GOOGLE_CLIENT_ID),
            client_id=GOOGLE_CLIENT_ID or None,
        )

    @router.post("/google", response_model=TokenResponse)
    def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
        try:
            profile = verify_google_credential(body.credential)
        except HTTPException:
            raise

        email = (profile.get("email") or "").strip().lower()
        google_sub = profile.get("sub") or ""
        full_name = (profile.get("full_name") or profile.get("name") or email.split("@")[0]).strip()
        if not email or not google_sub:
            raise HTTPException(status_code=400, detail="Google profile missing email")

        # Prefer PalmPay by email, else web Account (google_sub / email), then provision.
        pp = resolve_palmpay_by_email(db, email)
        web = db.execute(
            select(models.Account).where(
                (models.Account.google_sub == google_sub)
                | (func.lower(models.Account.email) == email)
            )
        ).scalar_one_or_none()

        if pp is None and web is None and body.intent == "login":
            raise HTTPException(
                status_code=404,
                detail="No member account found — please sign up first",
            )

        if web is None and pp is not None:
            web = ensure_web_account_for_palmpay(db, pp, commit=False)
            if web.google_sub is None:
                web.google_sub = google_sub
            web.email_verified = True

        if web is None:
            base_username = re.sub(r"[^a-z0-9_]", "_", email.split("@")[0].lower())[:32]
            if len(base_username) < 3:
                base_username = f"user_{secrets.token_hex(3)}"
            username = base_username
            suffix = 1
            while username_taken(db, username):
                username = f"{base_username[:28]}_{suffix}"
                suffix += 1
            try:
                persist_customer_account(
                    db,
                    email=email,
                    password_hash=hash_password(secrets.token_urlsafe(48)),
                    username=username,
                    full_name=full_name[:128],
                    email_verified=True,
                    google_sub=google_sub,
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            web = db.execute(
                select(models.Account).where(func.lower(models.Account.email) == email)
            ).scalar_one_or_none()
            if web is None:
                raise HTTPException(status_code=500, detail="Could not create Google account")

        else:
            if web.google_sub is None:
                web.google_sub = google_sub
            elif web.google_sub != google_sub:
                raise HTTPException(
                    status_code=409,
                    detail="This email is linked to a different Google account",
                )
            web.email_verified = True
            if full_name and not (web.full_name or "").strip():
                web.full_name = full_name[:128]

        if web.role in ("admin", "employee", "shop_owner"):
            raise HTTPException(
                status_code=403,
                detail=f"{web.role.replace('_', ' ').title()} accounts use the web portal, not the mobile wallet",
            )

        pp, wallet = ensure_palmpay_link_for_account(db, web, commit=False)
        if full_name and not (pp.full_name or "").strip():
            pp.full_name = full_name[:128]
        pp.email_verified = True
        if not pp.email:
            pp.email = email

        try:
            link_web_accounts_matching_palmpay(db, pp, commit=False)
        except Exception:
            logger.exception("link after Google auth failed for %s", email)

        # ensure_palmpay_link_for_account already created the wallet when needed
        if wallet is None:
            wallet = get_or_create_wallet(db, pp)
        access, refresh = issue_token_pair(db, pp)
        db.commit()
        db.refresh(wallet)
        db.refresh(pp)

        logger.info(
            "PalmPay Google %s ok email=%s palmpay_id=%s web_id=%s",
            body.intent,
            email,
            pp.id,
            web.id,
        )
        needs_spending = wallet.spending_pin_hash is None
        return token_response(
            pp,
            wallet,
            access,
            refresh,
            needs_login_pin_setup=not bool(pp.login_pin_hash),
            needs_spending_pin_setup=needs_spending,
        )
