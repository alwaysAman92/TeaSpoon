"""Scan + result-card endpoints (F1, F2, F5, F6-F9)."""
from __future__ import annotations

import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..schemas import ScanRequest, ScanResultOut
from ..services import scan_service

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("", response_model=ScanResultOut)
def scan_barcode(
    payload: ScanRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ScanResultOut:
    """Scan a barcode: translate, log to the ledger, return the full result card."""
    return scan_service.scan(
        db, user, barcode=payload.barcode, servings=payload.servings, log=payload.log,
    )


@router.get("/{barcode}", response_model=ScanResultOut)
def preview_barcode(
    barcode: str,
    date: Optional[str] = Query(None, description="ISO date (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ScanResultOut:
    """Preview a product without logging it (used for manual barcode entry)."""
    day = None
    if date:
        try:
            day = dt.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format; use YYYY-MM-DD.")
    return scan_service.scan(db, user, barcode=barcode, servings=1.0, log=False, day=day)
