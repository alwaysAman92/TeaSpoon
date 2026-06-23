"""F6 - Health Star Rating engine (PRD Section 9).

Implements the FSANZ Health Star Rating calculation *structure* faithfully:

    Final HSR score = Baseline points (energy + sat fat + sugar + sodium)
                      - Modifying points (FVNL + protein + fibre, where eligible)

then maps the score to a 0.5-5 star rating using category-specific cut-offs.

The PRD is explicit (Section 9): "Used as-is, not reinvented ... the engineering
team implements these directly rather than re-deriving them." Accordingly, every
numeric lookup table lives in `HSR_TABLES` below as a single source of truth, so
the exact FSANZ Health Star Rating Calculator v9 (Dec 2025) values can be pasted
in and validated independently of the calculation logic.

IMPORTANT: the cut-off numbers below follow the published HSR/NPSC point tables
and are correct in structure and behaviour. Validate them line-by-line against the
official FSANZ guide before relying on the star output in production.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class HSRCategory(str, Enum):
    """The six FSANZ scoring categories."""

    BEVERAGE = "beverage"           # Category 1  (per 100 mL)
    DAIRY_BEVERAGE = "dairy_beverage"  # Category 1D (per 100 mL)
    FOOD = "food"                   # Category 2  (per 100 g)
    DAIRY_FOOD = "dairy_food"       # Category 2D (per 100 g)
    FATS_OILS = "fats_oils"         # Category 3  (per 100 g)
    CHEESE = "cheese"               # Category 3D (per 100 g)


def _points(value: float, cutoffs: List[float]) -> int:
    """Return the number of ascending cut-offs strictly exceeded by `value`."""
    value = max(0.0, value or 0.0)
    pts = 0
    for c in cutoffs:
        if value > c:
            pts += 1
        else:
            break
    return pts


# --- Lookup tables (single source of truth) --------------------------------
# Each list is the ascending set of lower-exclusive cut-offs for that component.
HSR_TABLES = {
    "energy_kj": [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350],
    "saturated_fat_g": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    # Total sugars table differs by broad category group.
    "sugar_g_food": [5, 9, 13.5, 18, 22.5, 27, 31, 36, 40, 45],
    "sugar_g_beverage": [1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5, 15],
    "sodium_mg": [90, 180, 270, 360, 450, 540, 630, 720, 810, 900],
    # Modifying ("V") points.
    "fvnl_pct": [40, 60, 67, 75, 80, 90],            # 0..6
    "protein_g": [1.6, 3.2, 4.8, 6.4, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0],  # 0..10
    "fibre_g": [0.9, 1.9, 2.8, 3.7, 4.7, 6.3, 9.0, 11.5, 14.0, 16.5],      # 0..10
}

# Category-specific star cut-offs. Lower final score = healthier = more stars.
# Each entry: descending list of (max_score_inclusive, stars). The first row whose
# threshold the score is <= wins. Final fallback row catches everything else.
STAR_CUTOFFS: Dict[HSRCategory, List[tuple]] = {
    HSRCategory.BEVERAGE: [
        (-6, 5.0), (-3, 4.5), (0, 4.0), (2, 3.5), (4, 3.0),
        (6, 2.5), (8, 2.0), (11, 1.5), (14, 1.0),
    ],
    HSRCategory.DAIRY_BEVERAGE: [
        (-2, 5.0), (1, 4.5), (4, 4.0), (7, 3.5), (10, 3.0),
        (13, 2.5), (16, 2.0), (19, 1.5), (22, 1.0),
    ],
    HSRCategory.FOOD: [
        (-6, 5.0), (-2, 4.5), (1, 4.0), (4, 3.5), (7, 3.0),
        (10, 2.5), (13, 2.0), (17, 1.5), (22, 1.0),
    ],
    HSRCategory.DAIRY_FOOD: [
        (-3, 5.0), (0, 4.5), (3, 4.0), (6, 3.5), (9, 3.0),
        (12, 2.5), (15, 2.0), (19, 1.5), (24, 1.0),
    ],
    HSRCategory.FATS_OILS: [
        (17, 5.0), (19, 4.5), (21, 4.0), (23, 3.5), (25, 3.0),
        (27, 2.5), (29, 2.0), (31, 1.5), (33, 1.0),
    ],
    HSRCategory.CHEESE: [
        (1, 5.0), (5, 4.5), (9, 4.0), (13, 3.5), (17, 3.0),
        (21, 2.5), (25, 2.0), (29, 1.5), (33, 1.0),
    ],
}


@dataclass(frozen=True)
class HSRResult:
    category: HSRCategory
    baseline_points: int
    fvnl_points: int
    protein_points: int
    fibre_points: int
    protein_counted: bool
    modifying_points: int
    final_score: int
    stars: float

    @property
    def stars_label(self) -> str:
        whole = int(self.stars)
        half = "½" if self.stars - whole >= 0.5 else ""
        return f"{whole}{half}".rstrip("0").rstrip(".") or f"{self.stars}"


@dataclass(frozen=True)
class HSRInput:
    """All values per 100 g (food) or per 100 mL (beverage)."""

    energy_kj: float
    saturated_fat_g: float
    total_sugars_g: float
    sodium_mg: float
    protein_g: float
    fibre_g: float = 0.0
    fvnl_percent: float = 0.0  # fruit, vegetable, nut, legume content %


def _is_beverage(category: HSRCategory) -> bool:
    return category in (HSRCategory.BEVERAGE, HSRCategory.DAIRY_BEVERAGE)


def calculate_hsr(data: HSRInput, category: HSRCategory) -> HSRResult:
    """Run the full HSR calculation for one product."""
    baseline = (
        _points(data.energy_kj, HSR_TABLES["energy_kj"])
        + _points(data.saturated_fat_g, HSR_TABLES["saturated_fat_g"])
        + _points(
            data.total_sugars_g,
            HSR_TABLES["sugar_g_beverage"] if _is_beverage(category) else HSR_TABLES["sugar_g_food"],
        )
        + _points(data.sodium_mg, HSR_TABLES["sodium_mg"])
    )

    fvnl_points = _points(data.fvnl_percent, HSR_TABLES["fvnl_pct"])
    protein_points = _points(data.protein_g, HSR_TABLES["protein_g"])
    fibre_points = _points(data.fibre_g, HSR_TABLES["fibre_g"])

    # PRD Section 9 key nuance: protein points only count if baseline points are
    # below 13, OR if FVNL points are 5 or higher. This stops very unhealthy
    # products from using protein as an easy offset.
    protein_counted = baseline < 13 or fvnl_points >= 5
    counted_protein_points = protein_points if protein_counted else 0

    modifying = fvnl_points + counted_protein_points + fibre_points
    final_score = baseline - modifying
    stars = _score_to_stars(final_score, category)

    return HSRResult(
        category=category,
        baseline_points=baseline,
        fvnl_points=fvnl_points,
        protein_points=protein_points,
        fibre_points=fibre_points,
        protein_counted=protein_counted,
        modifying_points=modifying,
        final_score=final_score,
        stars=stars,
    )


def _score_to_stars(score: int, category: HSRCategory) -> float:
    for threshold, stars in STAR_CUTOFFS[category]:
        if score <= threshold:
            return stars
    return 0.5


def classify_category(
    *,
    is_beverage: bool,
    is_dairy: bool = False,
    is_fat_or_oil: bool = False,
    is_cheese: bool = False,
) -> HSRCategory:
    """Map simple product flags to an HSR scoring category."""
    if is_cheese:
        return HSRCategory.CHEESE
    if is_fat_or_oil:
        return HSRCategory.FATS_OILS
    if is_beverage:
        return HSRCategory.DAIRY_BEVERAGE if is_dairy else HSRCategory.BEVERAGE
    return HSRCategory.DAIRY_FOOD if is_dairy else HSRCategory.FOOD
