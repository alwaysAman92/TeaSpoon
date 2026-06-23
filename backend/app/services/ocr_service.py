"""OCR pipeline for label photos (PRD Section 10).

Two responsibilities, deliberately separated:

1. `run_ocr(image_bytes)` - calls Google Cloud Vision when a key is configured.
   This is the only part that touches an external service.
2. `parse_nutrition_text(text)` - a PURE, unit-tested function that pulls
   nutrient values out of OCR'd text, each with a confidence score. Low-confidence
   fields are gated by the caller and never go live (Section 10.1).

No user ever types a nutrient number anywhere in this flow.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

from ..config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class OCRField:
    value: float
    confidence: float


# Regexes for the standard FSSAI nutrition panel lines (per 100 g/serve).
_PATTERNS = {
    "energy_kj": r"energy[^0-9]*([\d.]+)\s*(kj|kcal|kcal)",
    "sugar_g": r"(?:total\s+)?sugar[s]?[^0-9]*([\d.]+)\s*g",
    "added_sugar_g": r"added\s+sugar[s]?[^0-9]*([\d.]+)\s*g",
    "saturated_fat_g": r"saturat\w*\s*fat[^0-9]*([\d.]+)\s*g",
    "total_fat_g": r"total\s*fat[^0-9]*([\d.]+)\s*g",
    "protein_g": r"protein[^0-9]*([\d.]+)\s*g",
    "fibre_g": r"(?:dietary\s+)?fib(?:re|er)[^0-9]*([\d.]+)\s*g",
    "sodium_mg": r"sodium[^0-9]*([\d.]+)\s*(mg|g)",
    "salt_g": r"salt[^0-9]*([\d.]+)\s*g",
}


def parse_nutrition_text(text: str, base_confidence: float = 0.85) -> Dict[str, OCRField]:
    """Extract nutrient fields from OCR text. Pure + deterministic."""
    text = (text or "").lower().replace(",", ".")
    out: Dict[str, OCRField] = {}

    for field, pattern in _PATTERNS.items():
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            value = float(match.group(1))
        except (ValueError, IndexError):
            continue

        # Energy reported as kcal -> convert to kJ.
        if field == "energy_kj" and match.lastindex and "kcal" in (match.group(2) or ""):
            value *= 4.184
        # Sodium reported in g -> mg.
        if field == "sodium_mg" and match.lastindex and (match.group(2) or "") == "g":
            value *= 1000.0
        # Salt -> sodium fallback.
        if field == "salt_g":
            out.setdefault("sodium_mg", OCRField(value / 2.5 * 1000.0, base_confidence - 0.1))
            continue

        # Confidence drops for implausible values (likely a misread).
        confidence = base_confidence
        if value < 0 or value > 100000:
            confidence = 0.3
        out[field] = OCRField(value, round(confidence, 2))

    return out


def run_ocr(image_bytes: bytes) -> Optional[str]:
    """Run OCR via Google Cloud Vision. Returns None if no key is configured."""
    if not settings.gcv_api_key:
        return None
    import base64

    import httpx

    payload = {
        "requests": [{
            "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
            "features": [{"type": "TEXT_DETECTION"}],
        }]
    }
    url = f"https://vision.googleapis.com/v1/images:annotate?key={settings.gcv_api_key}"
    try:
        resp = httpx.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data["responses"][0].get("fullTextAnnotation", {}).get("text", "")
    except (httpx.HTTPError, KeyError, IndexError):
        return None
