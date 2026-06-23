"""Settings endpoints - single flat screen (PRD 7.2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_out(user: models.User) -> SettingsOut:
    return SettingsOut(
        alternatives_priority=user.alternatives_priority,
        primary_nutrient=user.primary_nutrient,
        health_flags=user.health_flag_list,
        target_sugar_tsp=user.target_sugar_tsp,
        target_sodium_mg=user.target_sodium_mg,
        target_protein_g=user.target_protein_g,
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

    db.commit()
    db.refresh(user)
    return _to_out(user)
