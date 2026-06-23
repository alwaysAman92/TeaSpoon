"""Section 10 endpoints: label-photo submission + methodology note."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..services import contribution_service

router = APIRouter(prefix="/contributions", tags=["contributions"])

METHODOLOGY_NOTE = (
    "Verified data comes from official checks. Community data is shown with a "
    "confidence label until confirmed by matching submissions."
)


@router.post("/submit", status_code=201)
async def submit_label_photo(
    barcode: str = Form(...),
    photo: UploadFile = File(...),
    simulated_ocr_text: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    """Submit one label photo for an unknown barcode. No number entry exists.

    `simulated_ocr_text` is a dev-only aid so the pipeline can be exercised
    without a live Google Cloud Vision key.
    """
    image_bytes = await photo.read()
    submission, status = contribution_service.submit_photo(
        db,
        user=user,
        barcode=barcode,
        image_bytes=image_bytes,
        image_ref=photo.filename or "upload",
        simulated_text=simulated_ocr_text,
    )
    return {
        "submission_id": submission.id,
        "barcode": barcode,
        "min_confidence": submission.min_confidence,
        "trust_tier": status,
        "message": "Thanks - we'll confirm this once another photo matches.",
    }


@router.get("/methodology")
def methodology() -> dict:
    """Public in-app methodology note (Section 10.3)."""
    return {"note": METHODOLOGY_NOTE}


@router.get("/leaderboard")
def leaderboard(
    city: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list:
    """Top 20 contributors, optionally filtered by city or region (Section 10.4)."""
    query = db.query(models.User).filter(models.User.points > 0)
    if city:
        query = query.filter(models.User.city == city)
    if region:
        query = query.filter(models.User.region == region)
    users = query.order_by(models.User.points.desc()).limit(20).all()
    return [
        {
            "display_name": u.display_name or "Anonymous",
            "points": u.points or 0,
            "city": u.city,
            "region": u.region,
        }
        for u in users
    ]
