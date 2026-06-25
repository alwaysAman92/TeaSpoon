"""F9 - Ingredient & Veg/Non-Veg scanner.

Two India-specific jobs (PRD F9):
1. Translate cryptic INS additive codes into plain English.
2. Flag hidden non-veg ingredients (gelatin, animal rennet, lard, carmine)
   that the FSSAI green/brown dot can miss or mislabel.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

# A pragmatic subset of the INS/E additive dictionary, plain-English.
INS_ADDITIVES = {
    "100": "Curcumin (turmeric colour)",
    "101": "Riboflavin (vitamin B2, colour)",
    "120": "Carmine / cochineal (red colour - INSECT-DERIVED)",
    "129": "Allura Red AC (synthetic colour)",
    "150d": "Caramel colour (sulphite ammonia process)",
    "160a": "Beta-carotene (orange colour)",
    "163": "Anthocyanins (plant colour)",
    "211": "Sodium benzoate (preservative)",
    "223": "Sodium metabisulphite (preservative)",
    "296": "Malic acid (acidity regulator)",
    "300": "Ascorbic acid (vitamin C, antioxidant)",
    "322": "Lecithin (emulsifier)",
    "330": "Citric acid (acidity regulator)",
    "331": "Sodium citrate (acidity regulator)",
    "338": "Phosphoric acid (acidity regulator)",
    "407": "Carrageenan (thickener)",
    "415": "Xanthan gum (thickener)",
    "440": "Pectin (gelling agent)",
    "450": "Diphosphates (raising/stabiliser)",
    "460": "Cellulose (bulking agent)",
    "471": "Mono- & diglycerides of fatty acids (emulsifier - check source)",
    "476": "Polyglycerol polyricinoleate (emulsifier)",
    "500": "Sodium carbonates (raising agent)",
    "503": "Ammonium carbonates (raising agent)",
    "504": "Magnesium carbonate (anti-caking)",
    "508": "Potassium chloride (salt substitute)",
    "551": "Silicon dioxide (anti-caking)",
    "621": "Monosodium glutamate / MSG (flavour enhancer)",
    "627": "Disodium guanylate (flavour enhancer - often animal-derived)",
    "631": "Disodium inosinate (flavour enhancer - often animal-derived)",
    "635": "Disodium ribonucleotides (flavour enhancer)",
    "920": "L-cysteine (flour treatment - can be animal/hair-derived)",
    "1100": "Amylases (enzyme)",
    "1400": "Dextrin (modified starch)",
}

# Ingredients that are non-veg or commonly animal-derived (India-relevant).
NON_VEG_INGREDIENTS = {
    "gelatin": "Gelatin (from animal collagen)",
    "gelatine": "Gelatin (from animal collagen)",
    "rennet": "Animal rennet (from calf stomach)",
    "lard": "Lard (pork fat)",
    "tallow": "Tallow (beef/mutton fat)",
    "carmine": "Carmine (crushed cochineal insects)",
    "cochineal": "Cochineal (insect-derived red colour)",
    "shellac": "Shellac (insect-derived glaze)",
    "isinglass": "Isinglass (fish bladder)",
    "pepsin": "Pepsin (animal enzyme)",
    "anchovy": "Anchovy (fish)",
    "lipase": "Lipase (often animal-derived enzyme)",
}

AMBIGUOUS_INS = {"471", "627", "631", "920"}

# Common allergens (FSSAI / Codex Alimentarius major allergen list).
COMMON_ALLERGENS: dict[str, list[str]] = {
    "Milk / Dairy": ["milk", "cream", "butter", "cheese", "whey", "casein", "lactose", "curd", "paneer", "ghee"],
    "Peanuts": ["peanut", "groundnut"],
    "Tree Nuts": ["almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan", "macadamia", "brazil nut"],
    "Wheat / Gluten": ["wheat", "gluten", "maida", "atta", "semolina", "suji", "rawa", "barley", "rye", "oat"],
    "Soy": ["soy", "soya", "soybean", "soy lecithin"],
    "Egg": ["egg", "albumin", "lysozyme", "ovalbumin"],
    "Fish": ["fish", "anchovy", "sardine", "mackerel", "tuna", "cod"],
    "Crustaceans": ["shrimp", "prawn", "crab", "lobster", "crayfish"],
    "Sesame": ["sesame", "til"],
    "Mustard": ["mustard"],
    "Sulphites": ["sulphite", "sulfite", "sulphur dioxide", "sulfur dioxide", "metabisulphite", "metabisulfite"],
}

_INS_RE = re.compile(r"\b(?:ins|e)\s*[- ]?\s*(\d{3,4}[a-d]?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class AdditiveExplanation:
    code: str
    plain_english: str
    possibly_non_veg: bool


@dataclass(frozen=True)
class NonVegFlag:
    ingredient: str
    explanation: str


@dataclass(frozen=True)
class IngredientReport:
    additives: List[AdditiveExplanation]
    non_veg_flags: List[NonVegFlag]
    veg_status: str  # "veg" | "non_veg" | "uncertain"
    note: str
    allergens_detected: List[str]


def analyse_ingredients(
    ingredients_text: str,
    declared_veg: Optional[bool] = None,
) -> IngredientReport:
    # If ingredient text is missing or only whitespace, we cannot determine veg status.
    if not (ingredients_text or "").strip():
        return IngredientReport(
            additives=[],
            non_veg_flags=[],
            veg_status="unknown",
            note="Ingredient list not available -- cannot determine.",
            allergens_detected=[],
        )

    text = (ingredients_text or "").lower()

    additives: List[AdditiveExplanation] = []
    seen_codes = set()
    for match in _INS_RE.finditer(text):
        code = match.group(1).lower()
        if code in seen_codes:
            continue
        seen_codes.add(code)
        plain = INS_ADDITIVES.get(code, "Unrecognised additive code - look up on FSSAI list")
        additives.append(AdditiveExplanation(
            code=code.upper(),
            plain_english=plain,
            possibly_non_veg=code in AMBIGUOUS_INS or "insect" in plain.lower() or "animal" in plain.lower(),
        ))

    non_veg_flags: List[NonVegFlag] = []
    for needle, explanation in NON_VEG_INGREDIENTS.items():
        if re.search(rf"\b{re.escape(needle)}\b", text):
            non_veg_flags.append(NonVegFlag(ingredient=needle, explanation=explanation))

    has_hard_nonveg = len(non_veg_flags) > 0
    has_ambiguous = any(a.possibly_non_veg for a in additives)

    if has_hard_nonveg:
        veg_status = "non_veg"
        note = "Contains animal-derived ingredients the green/brown dot may not make obvious."
    elif has_ambiguous:
        veg_status = "uncertain"
        note = "Contains additives that can be animal-derived; source not declared."
    elif declared_veg is True:
        veg_status = "veg"
        note = "No non-veg ingredients detected; pack declares vegetarian."
    else:
        veg_status = "veg"
        note = "No animal-derived ingredients detected."

    # Allergen detection.
    allergens_detected: List[str] = []
    for allergen_name, keywords in COMMON_ALLERGENS.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                allergens_detected.append(allergen_name)
                break

    return IngredientReport(
        additives=additives,
        non_veg_flags=non_veg_flags,
        veg_status=veg_status,
        note=note,
        allergens_detected=allergens_detected,
    )
