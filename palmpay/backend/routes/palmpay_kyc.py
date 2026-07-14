"""PalmPay KYC submission (local file storage — no S3 in dev)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.palmpay_cnic import format_cnic, normalize_cnic
from backend.db import models
from backend.deps import get_db
from backend.deps_palmpay_auth import get_current_palmpay_account
from backend.settings import PALMPAY_DEV_AUTO_KYC, PALMPAY_KYC_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/palmpay/kyc", tags=["palmpay-kyc"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KycStatusResponse(BaseModel):
    status: str
    cnic_masked: str | None = None
    full_name: str
    message: str


class KycSubmitResponse(BaseModel):
    success: bool
    status: str
    cnic_masked: str
    message: str


async def _save_kyc_image(account_id: int, label: str, upload: UploadFile) -> str:
    suffix = Path(upload.filename or "img.jpg").suffix or ".jpg"
    dest_dir = PALMPAY_KYC_DIR / str(account_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{label}{suffix}"
    data = await upload.read()
    if len(data) < 1024:
        raise HTTPException(status_code=400, detail=f"{label} image is too small or empty")
    dest.write_bytes(data)
    return str(dest)


@router.get("/status", response_model=KycStatusResponse)
def kyc_status(
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> KycStatusResponse:
    row = db.execute(
        select(models.PalmPayKycSubmission)
        .where(models.PalmPayKycSubmission.account_id == account.id)
        .order_by(models.PalmPayKycSubmission.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    cnic_masked = None
    if row:
        cnic_masked = f"{row.cnic[:5]}*******{row.cnic[-1]}"

    return KycStatusResponse(
        status=account.kyc_status,
        cnic_masked=cnic_masked,
        full_name=account.full_name,
        message="KYC approved" if account.kyc_status == "approved" else "Complete KYC to continue",
    )


@router.post("/submit", response_model=KycSubmitResponse)
async def kyc_submit(
    full_name: str = Form(..., min_length=2, max_length=128),
    cnic: str = Form(..., min_length=13, max_length=20),
    front_image: UploadFile = File(...),
    back_image: UploadFile | None = File(default=None),
    account: models.PalmPayAccount = Depends(get_current_palmpay_account),
    db: Session = Depends(get_db),
) -> KycSubmitResponse:
    cnic_digits = normalize_cnic(cnic)
    if cnic_digits is None:
        raise HTTPException(status_code=400, detail="Invalid CNIC — enter 13 digits")

    front_path = await _save_kyc_image(account.id, "cnic_front", front_image)
    back_path = None
    if back_image is not None and back_image.filename:
        back_path = await _save_kyc_image(account.id, "cnic_back", back_image)

    status = "approved" if PALMPAY_DEV_AUTO_KYC else "pending"
    reviewed_at = _utcnow() if PALMPAY_DEV_AUTO_KYC else None

    account.full_name = full_name.strip()
    account.kyc_status = status

    db.add(
        models.PalmPayKycSubmission(
            account_id=account.id,
            cnic=cnic_digits,
            front_image_path=front_path,
            back_image_path=back_path,
            status=status,
            reviewed_at=reviewed_at,
        )
    )
    db.commit()

    logger.info("KYC submitted for account %s status=%s", account.id, status)

    return KycSubmitResponse(
        success=True,
        status=status,
        cnic_masked=format_cnic(cnic_digits),
        message="KYC approved — proceed to palm enrollment"
        if status == "approved"
        else "KYC submitted — pending manual review",
    )
