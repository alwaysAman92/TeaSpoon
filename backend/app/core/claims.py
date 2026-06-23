"""F8 - Misleading "Marketing vs Reality" claims detector.

Flags front-of-pack claims that contradict the actual nutrition data or FSSAI
claim thresholds. India-specific by design (PRD Section 3): checks Indian claim
language ("multigrain", "no added MSG") against the real numbers.

Thresholds reference FSSAI (Labelling & Display) Regulations 2020 nutrient-claim
criteria; values are per 100 g/mL unless noted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ClaimFinding:
    claim: str
    verdict: str          # "honest" | "misleading" | "unverifiable"
    explanation: str


@dataclass(frozen=True)
class ClaimsResult:
    findings: List[ClaimFinding]

    @property
    def has_misleading(self) -> bool:
        return any(f.verdict == "misleading" for f in self.findings)

    @property
    def badge(self) -> Optional[str]:
        if self.has_misleading:
            return "Marketing vs Reality"
        return None


# FSSAI / Codex-aligned nutrient claim thresholds (per 100 g for solids).
FSSAI_THRESHOLDS = {
    "low_sugar_g": 5.0,          # "low sugar" <= 5 g/100 g
    "no_added_sugar_g": 0.5,     # "no added sugar": no added sugars present
    "high_protein_g": 10.0,      # "high in protein": >= 10 g/100 g (>=20% energy)
    "source_protein_g": 5.0,     # "source of protein": >= 5 g/100 g
    "low_fat_g": 3.0,            # "low fat" <= 3 g/100 g
    "low_sodium_mg": 120.0,      # "low sodium" <= 120 mg/100 g
    "high_fibre_g": 6.0,         # "high fibre" >= 6 g/100 g
}


@dataclass(frozen=True)
class ClaimsInput:
    """Per-100g nutrition + the marketing strings printed on the pack."""

    front_of_pack_text: str
    sugar_g: float
    sodium_mg: float
    protein_g: float
    saturated_fat_g: float
    fibre_g: float = 0.0
    total_fat_g: float = 0.0
    added_sugar_g: Optional[float] = None
    ingredients_text: str = ""
    whole_grain_is_first: Optional[bool] = None


def _has(text: str, *needles: str) -> bool:
    t = text.lower()
    return any(n in t for n in needles)


def detect_claims(data: ClaimsInput) -> ClaimsResult:
    text = data.front_of_pack_text or ""
    ingredients = (data.ingredients_text or "").lower()
    findings: List[ClaimFinding] = []

    if _has(text, "high protein", "high in protein", "protein rich", "protein-rich"):
        if data.protein_g >= FSSAI_THRESHOLDS["high_protein_g"]:
            findings.append(ClaimFinding(
                "High protein", "honest",
                f"{data.protein_g:g} g/100 g meets the FSSAI 'high protein' bar (>=10 g).",
            ))
        else:
            findings.append(ClaimFinding(
                "High protein", "misleading",
                f"Only {data.protein_g:g} g protein/100 g - below the 10 g FSSAI threshold "
                f"for a 'high protein' claim.",
            ))

    if _has(text, "no added sugar", "no added sugars", "sugar free", "sugar-free", "zero sugar"):
        added = data.added_sugar_g
        sugary_ingredient = _has(
            ingredients, "sugar", "syrup", "honey", "jaggery", "maltodextrin",
            "dextrose", "fructose", "molasses", "concentrate",
        )
        if added is not None and added > FSSAI_THRESHOLDS["no_added_sugar_g"]:
            findings.append(ClaimFinding(
                "No added sugar", "misleading",
                f"{added:g} g of added sugar/100 g is listed despite the claim.",
            ))
        elif sugary_ingredient:
            findings.append(ClaimFinding(
                "No added sugar", "misleading",
                "A sugar/syrup-type ingredient appears in the list despite the claim.",
            ))
        elif data.sugar_g > 15:
            findings.append(ClaimFinding(
                "No added sugar", "misleading",
                f"Still {data.sugar_g:g} g total sugar/100 g - 'no added' hides naturally high sugar.",
            ))
        else:
            findings.append(ClaimFinding(
                "No added sugar", "honest",
                "No added-sugar ingredients detected.",
            ))

    if _has(text, "low sugar"):
        verdict = "honest" if data.sugar_g <= FSSAI_THRESHOLDS["low_sugar_g"] else "misleading"
        findings.append(ClaimFinding(
            "Low sugar", verdict,
            f"{data.sugar_g:g} g sugar/100 g vs the 5 g 'low sugar' threshold.",
        ))

    if _has(text, "multigrain", "multi-grain", "whole grain", "wholegrain", "whole wheat", "atta"):
        if data.whole_grain_is_first is False or _has(ingredients, "maida", "refined wheat flour", "refined flour"):
            findings.append(ClaimFinding(
                "Multigrain / whole grain", "misleading",
                "Refined flour (maida) appears as a main ingredient - the grain claim is cosmetic.",
            ))
        elif data.fibre_g and data.fibre_g < 3:
            findings.append(ClaimFinding(
                "Multigrain / whole grain", "misleading",
                f"Only {data.fibre_g:g} g fibre/100 g - low for a genuine whole-grain product.",
            ))
        else:
            findings.append(ClaimFinding(
                "Multigrain / whole grain", "unverifiable",
                "Grain claim is plausible but not confirmable from nutrition data alone.",
            ))

    if _has(text, "no added msg", "no msg", "no added m.s.g"):
        if _has(ingredients, "621", "monosodium glutamate", "msg", "yeast extract",
                "hydrolysed", "hydrolyzed", "flavour enhancer", "flavor enhancer"):
            findings.append(ClaimFinding(
                "No added MSG", "misleading",
                "A glutamate/flavour-enhancer source (e.g. INS 621, yeast extract) is present.",
            ))
        else:
            findings.append(ClaimFinding(
                "No added MSG", "honest", "No glutamate sources detected in the ingredients.",
            ))

    if _has(text, "low fat", "lite", "light"):
        if data.total_fat_g and data.total_fat_g > FSSAI_THRESHOLDS["low_fat_g"]:
            findings.append(ClaimFinding(
                "Low fat", "misleading",
                f"{data.total_fat_g:g} g fat/100 g exceeds the 3 g 'low fat' threshold.",
            ))

    if _has(text, "healthy", "guilt free", "guilt-free", "smart") and (
        data.sugar_g > 22.5 or data.sodium_mg > 600
    ):
        findings.append(ClaimFinding(
            "Healthy / guilt-free", "misleading",
            f"High sugar ({data.sugar_g:g} g) or sodium ({data.sodium_mg:g} mg) per 100 g "
            f"undercuts the wellness framing.",
        ))

    return ClaimsResult(findings=findings)
