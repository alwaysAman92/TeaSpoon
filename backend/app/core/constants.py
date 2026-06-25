"""Nutrition constants and default daily limits for TeaSpoon.

All translation math is centralised here so the numbers stay deterministic,
testable and auditable (PRD Section 11: "Deterministic, testable, auditable math").
"""
from __future__ import annotations

# --- Plain-language conversion factors -------------------------------------

# 1 level teaspoon of granulated sugar weighs ~4 g.
GRAMS_SUGAR_PER_TSP: float = 4.0

# 1 teaspoon of cooking oil / ghee weighs ~4.5 g of fat.
GRAMS_FAT_PER_TSP: float = 4.5

# WHO recommends < 2000 mg sodium per day for an adult (= 5 g salt).
WHO_SODIUM_LIMIT_MG: float = 2000.0

# Salt <-> sodium conversion (sodium x 2.5 = salt), kept for label parsing.
SODIUM_TO_SALT_FACTOR: float = 2.5


# --- Default daily targets (overridable per user in Settings) --------------
# Dashboard copy in the PRD: "6 of 10 tsp sugar", "60% of sodium limit",
# "38g of 70g protein goal" -> these defaults reproduce those headline numbers.

DEFAULT_DAILY_TARGETS = {
    "sugar_tsp": 10.0,            # ~40 g free sugar ceiling
    "sodium_mg": WHO_SODIUM_LIMIT_MG,
    "saturated_fat_tsp": 4.4,     # ~20 g saturated fat ceiling
    "protein_g": 70.0,            # fitness-leaning default (persona: Arjun)
    "fibre_g": 30.0,              # WHO adequate intake
}

# Health-profile adjustments (Phase 2). Multipliers/overrides applied on top
# of the defaults. Kept declarative so thresholds adjust per-user, not globally.
HEALTH_PROFILE_ADJUSTMENTS = {
    "diabetic": {"sugar_tsp": 6.0},          # tighter free-sugar ceiling
    "hypertensive": {"sodium_mg": 1500.0},   # AHA ideal limit
    "weight_goal": {"sugar_tsp": 6.0, "saturated_fat_tsp": 3.3},
}

# Field used as the "headline" nutrient on the result card, per product
# category. Falls back to whichever tracked nutrient is highest vs its limit.
HEADLINE_NUTRIENT_BY_CATEGORY = {
    "beverages": "sugar",
    "dairy_beverages": "sugar",
    "general_food": "sugar",
    "dairy_food": "saturated_fat",
    "fats_oils": "saturated_fat",
    "cheese": "sodium",
}


# Categories where serving size varies by use and must be asked, rather than
# assumed or defaulted. Maps category key -> list of quick-select presets
# (label, grams) plus a flag allowing custom gram entry.
VARIABLE_SERVING_CATEGORIES: dict[str, list[tuple[str, float]]] = {
    "spreads": [("1 tsp", 5.0), ("1 tbsp", 15.0), ("2 tbsp", 30.0)],
    "jams_honey": [("1 tsp", 5.0), ("1 tbsp", 15.0), ("2 tbsp", 30.0)],
    "oils_ghee": [("1 tsp", 5.0), ("1 tbsp", 15.0), ("2 tbsp", 30.0)],
    "sauces_condiments": [("1 tsp", 5.0), ("1 tbsp", 15.0), ("2 tbsp", 30.0)],
}
