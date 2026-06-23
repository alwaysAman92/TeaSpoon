"""F2 - Plain-Language Translation.

Converts raw label numbers (grams / milligrams) into units a person can act on
while standing in a shop aisle: teaspoons of sugar, % of the WHO sodium limit,
teaspoon-equivalents of ghee/oil, and protein grams against a daily target.

This module is pure and deterministic - no I/O, no DB - so it is trivially
unit-testable (PRD Phase 0).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import constants


def grams_sugar_to_tsp(sugar_g: float) -> float:
    """Convert grams of sugar to teaspoons (4 g per tsp)."""
    return _non_negative(sugar_g) / constants.GRAMS_SUGAR_PER_TSP


def grams_fat_to_tsp(fat_g: float) -> float:
    """Convert grams of (saturated) fat to ghee/oil teaspoon-equivalents."""
    return _non_negative(fat_g) / constants.GRAMS_FAT_PER_TSP


def sodium_mg_to_pct_limit(sodium_mg: float, limit_mg: Optional[float] = None) -> float:
    """Convert sodium (mg) to a percentage of the daily limit."""
    limit = limit_mg or constants.WHO_SODIUM_LIMIT_MG
    if limit <= 0:
        return 0.0
    return _non_negative(sodium_mg) / limit * 100.0


def salt_to_sodium_mg(salt_g: float) -> float:
    """Some labels report salt, not sodium. Convert salt (g) -> sodium (mg)."""
    return _non_negative(salt_g) / constants.SODIUM_TO_SALT_FACTOR * 1000.0


@dataclass(frozen=True)
class TranslatedNutrient:
    """One translated nutrient line for the result card."""

    key: str
    label: str
    raw_value: float
    raw_unit: str
    plain_value: float
    plain_unit: str
    headline: str  # e.g. "4.5 tsp of sugar"


@dataclass(frozen=True)
class Translation:
    """The full translated view of a single serving / 100g of a product."""

    basis: str  # "serving" or "per_100g"
    sugar: TranslatedNutrient
    sodium: TranslatedNutrient
    saturated_fat: TranslatedNutrient
    protein: TranslatedNutrient
    fibre: Optional[TranslatedNutrient] = None


def _round(value: float, places: int = 1) -> float:
    return round(value, places)


def translate(
    *,
    sugar_g: float,
    sodium_mg: float,
    saturated_fat_g: float,
    protein_g: float,
    fibre_g: Optional[float] = None,
    sodium_limit_mg: Optional[float] = None,
    protein_target_g: Optional[float] = None,
    basis: str = "serving",
) -> Translation:
    """Translate a set of raw nutrient values into plain-language nutrients."""
    sugar_tsp = _round(grams_sugar_to_tsp(sugar_g))
    sat_tsp = _round(grams_fat_to_tsp(saturated_fat_g))
    sodium_pct = _round(sodium_mg_to_pct_limit(sodium_mg, sodium_limit_mg))
    protein_target = protein_target_g or constants.DEFAULT_DAILY_TARGETS["protein_g"]

    sugar = TranslatedNutrient(
        key="sugar",
        label="Sugar",
        raw_value=_round(_non_negative(sugar_g)),
        raw_unit="g",
        plain_value=sugar_tsp,
        plain_unit="tsp",
        headline=f"{_fmt(sugar_tsp)} tsp of sugar",
    )
    sodium = TranslatedNutrient(
        key="sodium",
        label="Sodium",
        raw_value=_round(_non_negative(sodium_mg)),
        raw_unit="mg",
        plain_value=sodium_pct,
        plain_unit="% daily limit",
        headline=f"{_fmt(sodium_pct)}% of your daily sodium",
    )
    saturated_fat = TranslatedNutrient(
        key="saturated_fat",
        label="Saturated fat",
        raw_value=_round(_non_negative(saturated_fat_g)),
        raw_unit="g",
        plain_value=sat_tsp,
        plain_unit="tsp ghee/oil",
        headline=f"{_fmt(sat_tsp)} tsp of ghee",
    )
    protein = TranslatedNutrient(
        key="protein",
        label="Protein",
        raw_value=_round(_non_negative(protein_g)),
        raw_unit="g",
        plain_value=_round(_non_negative(protein_g)),
        plain_unit="g",
        headline=f"{_fmt(_non_negative(protein_g))}g of {_fmt(protein_target)}g protein",
    )

    fibre = None
    if fibre_g is not None:
        fibre = TranslatedNutrient(
            key="fibre",
            label="Fibre",
            raw_value=_round(_non_negative(fibre_g)),
            raw_unit="g",
            plain_value=_round(_non_negative(fibre_g)),
            plain_unit="g",
            headline=f"{_fmt(_non_negative(fibre_g))}g of fibre",
        )

    return Translation(
        basis=basis,
        sugar=sugar,
        sodium=sodium,
        saturated_fat=saturated_fat,
        protein=protein,
        fibre=fibre,
    )


def _non_negative(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    return max(0.0, float(value))


def _fmt(value: float) -> str:
    """Format a number without a trailing .0 (so '4 tsp' not '4.0 tsp')."""
    if float(value).is_integer():
        return str(int(value))
    return str(value)
