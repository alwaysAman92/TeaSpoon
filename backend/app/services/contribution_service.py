"""Section 10 trust-tier pipeline: photo submission -> OCR -> cross-match.

A barcode becomes a live product only when its OCR'd fields clear the confidence
gate; it is promoted from "pending" to "confirmed" when 2+ independent
submissions for the same barcode produce matching OCR results.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from ..schemas import ProductBase
from . import ocr_service, product_service

settings = get_settings()

# How close two submissions must be (relative) to count as "matching".
MATCH_TOLERANCE = 0.10


def _fields_to_columns(fields: Dict[str, "ocr_service.OCRField"]) -> Dict[str, Optional[float]]:
    gated: Dict[str, Optional[float]] = {}
    for key in ("sugar_g", "sodium_mg", "saturated_fat_g", "protein_g", "fibre_g", "energy_kj"):
        f = fields.get(key)
        # Confidence gate (Section 10.1): low-confidence fields held back.
        gated[key] = f.value if (f and f.confidence >= settings.ocr_min_confidence) else None
    return gated


def submit_photo(
    db: Session,
    *,
    user: models.User,
    barcode: str,
    image_bytes: bytes,
    image_ref: str,
    simulated_text: Optional[str] = None,
) -> Tuple[models.PhotoSubmission, str]:
    """Store a submission, OCR it, gate low-confidence fields, try cross-match."""
    text = simulated_text or ocr_service.run_ocr(image_bytes) or ""
    fields = ocr_service.parse_nutrition_text(text)
    cols = _fields_to_columns(fields)
    confidences = [f.confidence for f in fields.values()] or [0.0]
    min_conf = min(confidences)

    submission = models.PhotoSubmission(
        barcode=barcode,
        user_id=user.id,
        image_ref=image_ref,
        ocr_sugar_g=cols["sugar_g"],
        ocr_sodium_mg=cols["sodium_mg"],
        ocr_saturated_fat_g=cols["saturated_fat_g"],
        ocr_protein_g=cols["protein_g"],
        ocr_fibre_g=cols["fibre_g"],
        ocr_energy_kj=cols["energy_kj"],
        min_confidence=min_conf,
        status="ocr_done" if text else "gated",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    status = _try_promote(db, barcode)
    return submission, status


def _try_promote(db: Session, barcode: str) -> str:
    """Promote to a live product once submissions cross-match (Section 10.2)."""
    subs = (
        db.query(models.PhotoSubmission)
        .filter(models.PhotoSubmission.barcode == barcode, models.PhotoSubmission.status == "ocr_done")
        .all()
    )
    if not subs:
        return "pending"

    matched = _matching_group(subs)
    if len(matched) >= 2:
        agreed = _average(matched)
        product_service.upsert_from_base(
            db,
            ProductBase(
                barcode=barcode,
                name=f"Product {barcode}",
                sugar_g=agreed.get("sugar_g", 0.0) or 0.0,
                sodium_mg=agreed.get("sodium_mg", 0.0) or 0.0,
                saturated_fat_g=agreed.get("saturated_fat_g", 0.0) or 0.0,
                protein_g=agreed.get("protein_g", 0.0) or 0.0,
                fibre_g=agreed.get("fibre_g", 0.0) or 0.0,
                energy_kj=agreed.get("energy_kj", 0.0) or 0.0,
            ),
            source="community_confirmed",
            trust_tier="confirmed",
            note=f"confirmed by {len(matched)} matching submissions",
        )
        for s in matched:
            s.status = "matched"
        db.commit()
        return "confirmed"

    # A single usable submission -> create a pending product ("Unconfirmed").
    single = subs[0]
    product_service.upsert_from_base(
        db,
        ProductBase(
            barcode=barcode,
            name=f"Product {barcode}",
            sugar_g=single.ocr_sugar_g or 0.0,
            sodium_mg=single.ocr_sodium_mg or 0.0,
            saturated_fat_g=single.ocr_saturated_fat_g or 0.0,
            protein_g=single.ocr_protein_g or 0.0,
            fibre_g=single.ocr_fibre_g or 0.0,
            energy_kj=single.ocr_energy_kj or 0.0,
        ),
        source="community_pending",
        trust_tier="pending",
        note="single submission",
    )
    return "pending"


def _values(sub: models.PhotoSubmission) -> Dict[str, Optional[float]]:
    return {
        "sugar_g": sub.ocr_sugar_g,
        "sodium_mg": sub.ocr_sodium_mg,
        "saturated_fat_g": sub.ocr_saturated_fat_g,
        "protein_g": sub.ocr_protein_g,
    }


def _close(a: Optional[float], b: Optional[float]) -> bool:
    if a is None or b is None:
        return False
    if a == 0 and b == 0:
        return True
    denom = max(abs(a), abs(b), 1e-6)
    return abs(a - b) / denom <= MATCH_TOLERANCE


def _matching_group(subs: List[models.PhotoSubmission]) -> List[models.PhotoSubmission]:
    """Find the largest set of submissions whose key nutrients agree."""
    best: List[models.PhotoSubmission] = []
    for anchor in subs:
        group = [anchor]
        for other in subs:
            if other is anchor:
                continue
            av, ov = _values(anchor), _values(other)
            if all(_close(av[k], ov[k]) for k in ("sugar_g", "sodium_mg", "protein_g")):
                group.append(other)
        if len(group) > len(best):
            best = group
    return best


def _average(subs: List[models.PhotoSubmission]) -> Dict[str, float]:
    keys = ["sugar_g", "sodium_mg", "saturated_fat_g", "protein_g", "fibre_g", "energy_kj"]
    out: Dict[str, float] = {}
    for key in keys:
        vals = [getattr(s, f"ocr_{key}") for s in subs if getattr(s, f"ocr_{key}") is not None]
        if vals:
            out[key] = sum(vals) / len(vals)
    return out
