"""F7 - NOVA processing classification (groups 1-4).

NOVA groups foods by *extent and purpose of processing*, not nutrient content -
which is why it catches things HSR misses, e.g. a zero-sugar soda that scores
well on HSR but is still an ultra-processed Group 4 product (PRD F7).

We infer the group from ingredient markers. Open Food Facts also ships a
`nova_group` field; when present that is preferred and this acts as a fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# Markers of industrial formulation / cosmetic additives -> Group 4.
ULTRA_PROCESSED_MARKERS = [
    "high fructose corn syrup", "high-fructose corn syrup", "glucose syrup",
    "invert syrup", "maltodextrin", "hydrogenated", "hydrolysed", "hydrolyzed",
    "protein isolate", "whey protein concentrate", "soy protein isolate",
    "emulsifier", "stabiliser", "stabilizer", "thickener", "humectant",
    "flavour enhancer", "flavor enhancer", "monosodium glutamate", "msg",
    "artificial", "flavouring", "flavoring", "colour", "color", "modified starch",
    "anti-caking", "raising agent", "preservative", "sweetener", "aspartame",
    "acesulfame", "sucralose", "carrageenan",
]

# Markers of processed culinary ingredients added in cooking -> Group 2/3.
PROCESSED_CULINARY_MARKERS = ["salt", "sugar", "oil", "ghee", "butter", "vinegar", "honey"]

# INS / E additive codes always indicate a Group 4 formulation.
INS_PREFIXES = ("ins", "e")


class NovaGroup(int):
    pass


@dataclass(frozen=True)
class NovaResult:
    group: Optional[int]  # 1..4 or None for unknown
    label: str
    tag: str    # short chip text for the result card
    rationale: str


_GROUP_META = {
    1: ("Unprocessed", "NOVA 1 · Whole", "Whole or minimally processed food."),
    2: ("Culinary ingredient", "NOVA 2 · Culinary", "A processed culinary ingredient (oil, sugar, salt)."),
    3: ("Processed", "NOVA 3 · Processed", "A processed food made by adding salt/sugar/oil to whole foods."),
    4: ("Ultra-processed", "NOVA 4 · Ultra-processed", "Industrial formulation with additives not used in home cooking."),
}


def _contains_additive_code(token: str) -> bool:
    token = token.strip().lower().replace("(", "").replace(")", "")
    if token.startswith("ins"):
        return any(ch.isdigit() for ch in token)
    # An "E" followed by digits (E621) is an additive; a lone "e" is not.
    if token.startswith("e") and len(token) > 1 and token[1:].split()[0].isdigit():
        return True
    return False


def classify_nova(
    ingredients_text: Optional[str] = None,
    ingredients_list: Optional[List[str]] = None,
    off_nova_group: Optional[int] = None,
) -> NovaResult:
    """Classify a product into a NOVA group."""
    if off_nova_group in (1, 2, 3, 4):
        return _result(int(off_nova_group))

    # If no OFF nova group and no ingredient information, classification is unknown.
    if off_nova_group is None:
        # ingredients_text may be None or empty/whitespace only, and ingredients_list may be None or empty.
        txt = (ingredients_text or "").strip()
        lst = ingredients_list or []
        if not txt and len(lst) == 0:
            return NovaResult(group=None, label="Unknown", tag="NOVA · Unknown", rationale="Not enough ingredient data to classify processing level.")

    text = (ingredients_text or "").lower()
    tokens = ingredients_list or [t.strip() for t in text.replace(";", ",").split(",") if t.strip()]

    # Any additive code or ultra-processing marker -> Group 4.
    if any(_contains_additive_code(t) for t in tokens):
        return _result(4)
    if any(marker in text for marker in ULTRA_PROCESSED_MARKERS):
        return _result(4)

    n_ingredients = len([t for t in tokens if t])
    has_culinary = any(m in text for m in PROCESSED_CULINARY_MARKERS)

    if n_ingredients == 0:
        return _result(1)
    if n_ingredients == 1:
        # A single culinary ingredient (e.g. "sunflower oil") is Group 2.
        return _result(2 if has_culinary else 1)
    if has_culinary and n_ingredients <= 4:
        return _result(3)
    if n_ingredients <= 2:
        return _result(1)
    return _result(3)


def _result(group: int) -> NovaResult:
    label, tag, rationale = _GROUP_META[group]
    return NovaResult(group=group, label=label, tag=tag, rationale=rationale)
