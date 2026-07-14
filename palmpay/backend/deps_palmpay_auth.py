"""PalmPay auth dependency."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.auth.palmpay_tokens import decode_palmpay_access_token
from backend.db import models
from backend.deps import get_db

_bearer = HTTPBearer(auto_error=False)


def get_current_palmpay_account(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> models.PalmPayAccount:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_palmpay_access_token(creds.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    account = db.get(models.PalmPayAccount, int(payload["sub"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Account not found")
    return account
