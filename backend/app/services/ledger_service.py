"""Daily ledger persistence + dashboard assembly (F3/F4)."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..core import ledger
from ..core.translation import grams_sugar_to_tsp
from ..schemas import DashboardOut, NutrientProgressOut, RecentScanOut


def _today() -> dt.date:
    return dt.date.today()


def log_scan(
    db: Session,
    *,
    user: models.User,
    product: models.Product,
    servings: float,
) -> models.ScanLog:
    """Persist a scan's contribution to today's ledger (per-100g -> per-serving)."""
    factor = (product.serving_size_g or 100.0) / 100.0 * max(0.0, servings)
    entry = models.ScanLog(
        user_id=user.id,
        product_id=product.id,
        log_date=_today(),
        servings=servings,
        sugar_g=product.sugar_g * factor,
        sodium_mg=product.sodium_mg * factor,
        saturated_fat_g=product.saturated_fat_g * factor,
        protein_g=product.protein_g * factor,
        fibre_g=product.fibre_g * factor,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def totals_for_day(db: Session, user_id: int, day: Optional[dt.date] = None) -> ledger.DailyTotals:
    day = day or _today()
    row = (
        db.query(
            func.coalesce(func.sum(models.ScanLog.sugar_g), 0.0),
            func.coalesce(func.sum(models.ScanLog.sodium_mg), 0.0),
            func.coalesce(func.sum(models.ScanLog.saturated_fat_g), 0.0),
            func.coalesce(func.sum(models.ScanLog.protein_g), 0.0),
            func.coalesce(func.sum(models.ScanLog.fibre_g), 0.0),
        )
        .filter(models.ScanLog.user_id == user_id, models.ScanLog.log_date == day)
        .one()
    )
    return ledger.DailyTotals(
        sugar_g=row[0], sodium_mg=row[1], saturated_fat_g=row[2],
        protein_g=row[3], fibre_g=row[4],
    )


def scans_count(db: Session, user_id: int, day: Optional[dt.date] = None) -> int:
    day = day or _today()
    return (
        db.query(func.count(models.ScanLog.id))
        .filter(models.ScanLog.user_id == user_id, models.ScanLog.log_date == day)
        .scalar()
    ) or 0


def _user_targets(user: models.User) -> Dict[str, float]:
    overrides = {
        "sugar_tsp": user.target_sugar_tsp,
        "sodium_mg": user.target_sodium_mg,
        "protein_g": user.target_protein_g,
    }
    overrides = {k: v for k, v in overrides.items() if v is not None}
    return ledger.resolve_targets_for_profile(user.health_flag_list, overrides)


def build_dashboard(db: Session, user: models.User, day: Optional[dt.date] = None) -> DashboardOut:
    day = day or _today()
    totals = totals_for_day(db, user.id, day)
    targets = _user_targets(user)
    dash = ledger.build_dashboard(totals, targets, primary_key=user.primary_nutrient)

    return DashboardOut(
        date=day.isoformat(),
        primary=_progress_out(dash.primary),
        secondary=[_progress_out(s) for s in dash.secondary],
        takeaway=dash.takeaway,
        scans_today=scans_count(db, user.id, day),
        streak=current_streak(db, user.id, day),
        recent=_recent_scans(db, user.id, day),
    )


def current_streak(db: Session, user_id: int, end_day: Optional[dt.date] = None, cap: int = 365) -> int:
    """Consecutive days (ending at end_day) with at least one logged scan."""
    day = end_day or _today()
    streak = 0
    while streak < cap and scans_count(db, user_id, day) > 0:
        streak += 1
        day = day - dt.timedelta(days=1)
    return streak


def _recent_scans(db: Session, user_id: int, day: dt.date, limit: int = 12) -> List[RecentScanOut]:
    rows = (
        db.query(models.ScanLog, models.Product)
        .join(models.Product, models.Product.id == models.ScanLog.product_id)
        .filter(models.ScanLog.user_id == user_id, models.ScanLog.log_date == day)
        .order_by(models.ScanLog.id.desc())
        .limit(limit)
        .all()
    )
    out: List[RecentScanOut] = []
    for log, product in rows:
        out.append(RecentScanOut(
            name=product.name,
            brand=product.brand,
            category=product.category,
            image_url=product.image_url,
            logged_at=(log.created_at.isoformat() if log.created_at else day.isoformat()),
            sugar_tsp=round(grams_sugar_to_tsp(log.sugar_g), 1),
            sodium_mg=round(log.sodium_mg, 0),
            protein_g=round(log.protein_g, 1),
        ))
    return out


def trend_last_n_days(db: Session, user: models.User, n: int = 7) -> List[dict]:
    """7-day trend (F4): primary nutrient consumed per day."""
    targets = _user_targets(user)
    out: List[dict] = []
    today = _today()
    for offset in range(n - 1, -1, -1):
        day = today - dt.timedelta(days=offset)
        totals = totals_for_day(db, user.id, day)
        dash = ledger.build_dashboard(totals, targets, primary_key=user.primary_nutrient)
        out.append({
            "date": day.isoformat(),
            "value": dash.primary.consumed,
            "pct": dash.primary.pct,
        })
    return out


def _progress_out(p: ledger.NutrientProgress) -> NutrientProgressOut:
    return NutrientProgressOut(
        key=p.key, label=p.label, consumed=p.consumed, target=p.target,
        unit=p.unit, pct=p.pct, is_goal=p.is_goal, headline=p.headline,
    )
