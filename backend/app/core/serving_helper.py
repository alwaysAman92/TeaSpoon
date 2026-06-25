from __future__ import annotations

from typing import List, Optional, Dict

from .constants import VARIABLE_SERVING_CATEGORIES

_SPREAD_HINTS = ("peanut butter", "nut butter", "spread", "mayo", "mayonnaise")
_JAM_HINTS = ("jam", "honey", "marmalade", "jelly", "preserve", "chutney")
_OIL_HINTS = ("oil", "ghee", "butter", "margarine", "lard", "fat", "vanaspati")
_SAUCE_HINTS = ("sauce", "ketchup", "dip", "dressing", "vinegar", "mustard", "relish", "syrup")


def detect_variable_category(
    name: str,
    tags: List[str] | None = None,
    category: str | None = None,
) -> Optional[str]:
    name = (name or "").lower()
    joined_tags = " ".join(tags or []).lower()
    category = (category or "").lower()

    # spreads
    if (
        any(h in name or h in joined_tags for h in _SPREAD_HINTS)
        or "spreads" in joined_tags
        or "mayonnaises" in joined_tags
        or "nut-butters" in joined_tags
        or category == "spreads"
    ):
        return "spreads"

    # jams_honey
    if (
        any(h in name or h in joined_tags for h in _JAM_HINTS)
        or "jams" in joined_tags
        or "honeys" in joined_tags
        or "marmalades" in joined_tags
        or category == "jams_honey"
    ):
        return "jams_honey"

    # oils_ghee
    if (
        any(h in name or h in joined_tags for h in _OIL_HINTS)
        or "oils" in joined_tags
        or "fats" in joined_tags
        or "ghees" in joined_tags
        or category == "fats_oils"
        or category == "oils_ghee"
    ):
        return "oils_ghee"

    # sauces_condiments
    if (
        any(h in name or h in joined_tags for h in _SAUCE_HINTS)
        or "sauces" in joined_tags
        or "condiments" in joined_tags
        or "syrups" in joined_tags
        or category == "sauces_condiments"
    ):
        return "sauces_condiments"

    return None


def needs_serving_input(
    name: str,
    tags: List[str] | None = None,
    category: str | None = None,
) -> bool:
    return detect_variable_category(name, tags, category) is not None


def get_serving_presets(name: str, category: str | None = None) -> List[Dict[str, float]]:
    cat_key = detect_variable_category(name, category=category)
    if not cat_key:
        return []
    presets = VARIABLE_SERVING_CATEGORIES.get(cat_key, [])
    return [{"label": label, "grams": grams} for label, grams in presets]
