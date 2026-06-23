"""F5 - Alternatives on every scan.

Shown on *every* scan, good or bad - every scan ends in a next action, not a
verdict (PRD F5). Two modes set once in Settings:

* Healthier (default): rank same-category products by lower sugar/sodium/sat-fat
  and better protein density, regardless of price.
* Cheaper: rank by lower price among products of comparable nutrition quality
  (within ~10% of the scanned product's HSR score) in the same category.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AltCandidate:
    """Minimal view of a product needed to rank it as an alternative."""

    id: int
    name: str
    brand: Optional[str]
    category: str
    sugar_g: float
    sodium_mg: float
    saturated_fat_g: float
    protein_g: float
    hsr_stars: float
    price_inr: Optional[float] = None
    image_url: Optional[str] = None


@dataclass(frozen=True)
class RankedAlternative:
    candidate: AltCandidate
    reason: str
    score: float


def _health_score(p: AltCandidate) -> float:
    """Lower is healthier. Protein density (good) reduces the score."""
    return (
        p.sugar_g * 1.0
        + p.sodium_mg * 0.01
        + p.saturated_fat_g * 1.5
        - p.protein_g * 0.8
    )


def _healthier_reason(scanned: AltCandidate, alt: AltCandidate) -> str:
    parts: List[str] = []
    if alt.sugar_g < scanned.sugar_g - 0.5:
        parts.append(f"{scanned.sugar_g - alt.sugar_g:.0f}g less sugar")
    if alt.sodium_mg < scanned.sodium_mg - 20:
        parts.append(f"{(scanned.sodium_mg - alt.sodium_mg):.0f}mg less sodium")
    if alt.protein_g > scanned.protein_g + 0.5:
        parts.append(f"{alt.protein_g - scanned.protein_g:.0f}g more protein")
    if alt.hsr_stars > scanned.hsr_stars:
        parts.append(f"{alt.hsr_stars:g}★ vs {scanned.hsr_stars:g}★")
    return ", ".join(parts[:2]) if parts else "A cleaner pick in the same aisle"


def _cheaper_reason(scanned: AltCandidate, alt: AltCandidate) -> str:
    if alt.price_inr is not None and scanned.price_inr:
        saving = scanned.price_inr - alt.price_inr
        if saving > 0:
            return f"₹{saving:.0f} cheaper, similar health score"
    return "Cheaper at a comparable health score"


def rank_alternatives(
    scanned: AltCandidate,
    candidates: List[AltCandidate],
    mode: str = "healthier",
    limit: int = 3,
) -> List[RankedAlternative]:
    """Return up to `limit` ranked alternatives for the scanned product."""
    same_category = [
        c for c in candidates
        if c.category == scanned.category and c.id != scanned.id
    ]

    if mode == "cheaper":
        return _rank_cheaper(scanned, same_category, limit)
    return _rank_healthier(scanned, same_category, limit)


def _rank_healthier(scanned, pool, limit):
    scanned_score = _health_score(scanned)
    ranked = []
    for c in pool:
        score = _health_score(c)
        # Only suggest genuinely-better-or-equal options.
        if score <= scanned_score + 0.001:
            ranked.append(RankedAlternative(c, _healthier_reason(scanned, c), score))
    ranked.sort(key=lambda r: r.score)
    return ranked[:limit]


def _rank_cheaper(scanned, pool, limit):
    # Comparable nutrition = within ~10% of scanned HSR (min half-star band).
    band = max(0.5, scanned.hsr_stars * 0.10)
    comparable = [
        c for c in pool
        if c.price_inr is not None
        and abs(c.hsr_stars - scanned.hsr_stars) <= band
        and (scanned.price_inr is None or c.price_inr < scanned.price_inr)
    ]
    comparable.sort(key=lambda c: c.price_inr)
    return [RankedAlternative(c, _cheaper_reason(scanned, c), c.price_inr) for c in comparable[:limit]]
