"""Settings endpoints - single flat screen (PRD 7.2)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _badges_for(user: models.User) -> List[str]:
    """Compute dynamic badges based on contributor points (Section 10.4)."""
    badges: List[str] = []
    points = user.points or 0
    if points >= 1:
        badges.append("Contributor")
    if points >= 500:
        badges.append("Bronze Spoon")
    if points >= 2000:
        badges.append("Silver Spoon")
    if points >= 5000:
        badges.append("Gold Spoon")
    if points >= 10000:
        badges.append("Diamond Spoon")
    return badges


def _to_out(user: models.User) -> SettingsOut:
    return SettingsOut(
        alternatives_priority=user.alternatives_priority,
        primary_nutrient=user.primary_nutrient,
        health_flags=user.health_flag_list,
        target_sugar_tsp=user.target_sugar_tsp,
        target_sodium_mg=user.target_sodium_mg,
        target_protein_g=user.target_protein_g,
        points=user.points or 0,
        city=user.city,
        region=user.region,
        badges=_badges_for(user),
    )


@router.get("", response_model=SettingsOut)
def get_settings(user: models.User = Depends(get_current_user)) -> SettingsOut:
    return _to_out(user)


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> SettingsOut:
    if payload.alternatives_priority is not None:
        user.alternatives_priority = payload.alternatives_priority
    if payload.primary_nutrient is not None:
        user.primary_nutrient = payload.primary_nutrient
    if payload.health_flags is not None:
        allowed = {"diabetic", "hypertensive", "weight_goal", "allergy"}
        user.health_flags = ",".join(f for f in payload.health_flags if f in allowed)
    if payload.target_sugar_tsp is not None:
        user.target_sugar_tsp = payload.target_sugar_tsp
    if payload.target_sodium_mg is not None:
        user.target_sodium_mg = payload.target_sodium_mg
    if payload.target_protein_g is not None:
        user.target_protein_g = payload.target_protein_g
    if payload.city is not None:
        user.city = payload.city.strip() or None
    if payload.region is not None:
        user.region = payload.region.strip() or None

    db.commit()
    db.refresh(user)
    return _to_out(user)
