"""F3/F4 - Daily Ledger + Dashboard maths.

Every scan silently adds its nutrients to the user's running daily totals.
This module computes totals, progress vs. target, and the single bold
one-line takeaway shown on the dashboard. Pure + deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import constants
from .translation import grams_fat_to_tsp, grams_sugar_to_tsp


@dataclass
class ScanEntry:
    """A single logged scan's contribution to the day, in raw units."""

    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    saturated_fat_g: float = 0.0
    protein_g: float = 0.0
    fibre_g: float = 0.0


@dataclass
class DailyTotals:
    """Accumulated raw totals for one user-day."""

    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    saturated_fat_g: float = 0.0
    protein_g: float = 0.0
    fibre_g: float = 0.0

    def add(self, entry: ScanEntry) -> "DailyTotals":
        self.sugar_g += max(0.0, entry.sugar_g)
        self.sodium_mg += max(0.0, entry.sodium_mg)
        self.saturated_fat_g += max(0.0, entry.saturated_fat_g)
        self.protein_g += max(0.0, entry.protein_g)
        self.fibre_g += max(0.0, entry.fibre_g)
        return self


@dataclass
class NutrientProgress:
    """Progress of one nutrient toward (or against) its daily target."""

    key: str
    label: str
    consumed: float
    target: float
    unit: str
    pct: float          # 0..100+ (capped display handled in UI)
    is_goal: bool       # True for protein/fibre (more is good)
    headline: str       # e.g. "6 of 10 tsp sugar"


@dataclass
class Dashboard:
    primary: NutrientProgress
    secondary: List[NutrientProgress] = field(default_factory=list)
    takeaway: str = ""


def _targets(overrides: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    targets = dict(constants.DEFAULT_DAILY_TARGETS)
    if overrides:
        targets.update({k: v for k, v in overrides.items() if v is not None})
    return targets


def resolve_targets_for_profile(
    health_flags: Optional[List[str]] = None,
    overrides: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Phase 2: adjust daily thresholds per health profile (tightest wins)."""
    targets = _targets(overrides)
    for flag in health_flags or []:
        adjustment = constants.HEALTH_PROFILE_ADJUSTMENTS.get(flag, {})
        for key, value in adjustment.items():
            # For ceilings (sugar/sodium/fat) the tighter (lower) limit wins.
            targets[key] = min(targets.get(key, value), value)
    return targets


def _pct(consumed: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return round(consumed / target * 100.0, 1)


def _fmt(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(round(value, 1))


def build_dashboard(
    totals: DailyTotals,
    targets: Optional[Dict[str, float]] = None,
    primary_key: str = "sugar",
) -> Dashboard:
    """Turn raw daily totals into the dashboard view model."""
    t = targets or _targets()

    sugar_tsp = round(grams_sugar_to_tsp(totals.sugar_g), 1)
    sat_tsp = round(grams_fat_to_tsp(totals.saturated_fat_g), 1)
    sodium_pct = _pct(totals.sodium_mg, t["sodium_mg"])

    progress = {
        "sugar": NutrientProgress(
            key="sugar",
            label="Sugar",
            consumed=sugar_tsp,
            target=t["sugar_tsp"],
            unit="tsp",
            pct=_pct(sugar_tsp, t["sugar_tsp"]),
            is_goal=False,
            headline=f"{_fmt(sugar_tsp)} of {_fmt(t['sugar_tsp'])} tsp sugar",
        ),
        "sodium": NutrientProgress(
            key="sodium",
            label="Sodium",
            consumed=round(totals.sodium_mg, 0),
            target=t["sodium_mg"],
            unit="mg",
            pct=sodium_pct,
            is_goal=False,
            headline=f"{_fmt(sodium_pct)}% of sodium limit",
        ),
        "protein": NutrientProgress(
            key="protein",
            label="Protein",
            consumed=round(totals.protein_g, 1),
            target=t["protein_g"],
            unit="g",
            pct=_pct(totals.protein_g, t["protein_g"]),
            is_goal=True,
            headline=f"{_fmt(round(totals.protein_g,1))}g of {_fmt(t['protein_g'])}g protein goal",
        ),
        "saturated_fat": NutrientProgress(
            key="saturated_fat",
            label="Saturated fat",
            consumed=sat_tsp,
            target=t["saturated_fat_tsp"],
            unit="tsp",
            pct=_pct(sat_tsp, t["saturated_fat_tsp"]),
            is_goal=False,
            headline=f"{_fmt(sat_tsp)} of {_fmt(t['saturated_fat_tsp'])} tsp ghee",
        ),
        "fibre": NutrientProgress(
            key="fibre",
            label="Fibre",
            consumed=round(totals.fibre_g, 1),
            target=t["fibre_g"],
            unit="g",
            pct=_pct(totals.fibre_g, t["fibre_g"]),
            is_goal=True,
            headline=f"{_fmt(round(totals.fibre_g,1))}g of {_fmt(t['fibre_g'])}g fibre",
        ),
    }

    primary = progress.get(primary_key, progress["sugar"])
    secondary_order = [k for k in ("sodium", "protein", "fibre", "saturated_fat") if k != primary_key]
    secondary = [progress[k] for k in secondary_order]

    return Dashboard(primary=primary, secondary=secondary, takeaway=_takeaway(primary))


def _takeaway(primary: NutrientProgress) -> str:
    """One bold one-line takeaway, styled like a Fix My Itch headline."""
    pct = primary.pct
    if primary.is_goal:
        if pct >= 100:
            return f"You hit your {primary.label.lower()} goal today."
        if pct <= 0:
            return f"No {primary.label.lower()} logged yet today."
        return f"You're {int(pct)}% to your {primary.label.lower()} goal."
    # Ceiling nutrient (sugar/sodium/fat)
    if pct <= 0:
        return "A clean slate. Nothing logged yet today."
    if pct < 80:
        return f"You're {int(pct)}% through your {primary.label.lower()} budget."
    if pct < 100:
        return f"Careful - {int(pct)}% of your {primary.label.lower()} budget gone."
    return f"Over budget - {int(pct)}% of your {primary.label.lower()} for today."
