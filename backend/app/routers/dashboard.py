"""Daily dashboard endpoints (F4)."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..schemas import DashboardOut
from ..services import ledger_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(
    date: Optional[str] = Query(None, description="ISO date (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> DashboardOut:
    day = None
    if date:
        try:
            day = dt.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD.")
    return ledger_service.build_dashboard(db, user, day=day)


@router.get("/trend")
def trend(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[dict]:
    """7-day (default) trend line for the primary nutrient."""
    return ledger_service.trend_last_n_days(db, user, n=days)
