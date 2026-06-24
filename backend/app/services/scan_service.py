"""Scan orchestration (PRD Section 11.1 request flow).

Ties together translation (F2), ledger (F3/F4), alternatives (F5) and the
tap-for-details layer (F6-F9) into a single result-card payload.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from .. import models
from ..core import claims as claims_core
from ..core import constants
from ..core import hsr as hsr_core
from ..core import ingredients as ing_core
from ..core import nova as nova_core
from ..core import translation as tr_core
from ..core.alternatives import AltCandidate, rank_alternatives
from ..schemas import (
    AdditiveOut,
    AlternativeOut,
    ClaimOut,
    ClaimsOut,
    DetailLayerOut,
    HSROut,
    IngredientsOut,
    NonVegFlagOut,
    NovaOut,
    ProductOut,
    ScanResultOut,
    TranslatedNutrientOut,
)
from . import ledger_service, product_service


def _hsr_for(product: models.Product) -> hsr_core.HSRResult:
    category = hsr_core.classify_category(
        is_beverage=product.is_beverage,
        is_dairy=product.is_dairy,
        is_fat_or_oil=product.is_fat_or_oil,
        is_cheese=product.is_cheese,
    )
    data = hsr_core.HSRInput(
        energy_kj=product.energy_kj,
        saturated_fat_g=product.saturated_fat_g,
        total_sugars_g=product.sugar_g,
        sodium_mg=product.sodium_mg,
        protein_g=product.protein_g,
        fibre_g=product.fibre_g,
        fvnl_percent=product.fvnl_percent,
    )
    return hsr_core.calculate_hsr(data, category)


def _to_candidate(product: models.Product, stars: float) -> AltCandidate:
    return AltCandidate(
        id=product.id,
        name=product.name,
        brand=product.brand,
        category=product.category,
        sugar_g=product.sugar_g,
        sodium_mg=product.sodium_mg,
        saturated_fat_g=product.saturated_fat_g,
        protein_g=product.protein_g,
        hsr_stars=stars,
        price_inr=product.price_inr,
        image_url=product.image_url,
    )


def _headline_key(product: models.Product) -> str:
    return constants.HEADLINE_NUTRIENT_BY_CATEGORY.get(product.category, "sugar")


def build_detail_layer(product: models.Product, hsr_result: hsr_core.HSRResult) -> DetailLayerOut:
    nova = nova_core.classify_nova(
        ingredients_text=product.ingredients_text,
        off_nova_group=product.nova_group,
    )
    claim_result = claims_core.detect_claims(claims_core.ClaimsInput(
        front_of_pack_text=f"{product.name} {product.front_of_pack_text}",
        sugar_g=product.sugar_g,
        sodium_mg=product.sodium_mg,
        protein_g=product.protein_g,
        saturated_fat_g=product.saturated_fat_g,
        fibre_g=product.fibre_g,
        total_fat_g=product.total_fat_g,
        added_sugar_g=product.added_sugar_g,
        ingredients_text=product.ingredients_text,
    ))
    report = ing_core.analyse_ingredients(product.ingredients_text, product.declared_veg)

    return DetailLayerOut(
        hsr=HSROut(
            stars=hsr_result.stars,
            final_score=hsr_result.final_score,
            baseline_points=hsr_result.baseline_points,
            modifying_points=hsr_result.modifying_points,
            protein_counted=hsr_result.protein_counted,
        ),
        nova=NovaOut(group=nova.group, label=nova.label, tag=nova.tag, rationale=nova.rationale),
        claims=ClaimsOut(
            badge=claim_result.badge,
            findings=[ClaimOut(claim=f.claim, verdict=f.verdict, explanation=f.explanation)
                      for f in claim_result.findings],
        ),
        ingredients=IngredientsOut(
            veg_status=report.veg_status,
            note=report.note,
            additives=[AdditiveOut(code=a.code, plain_english=a.plain_english,
                                   possibly_non_veg=a.possibly_non_veg) for a in report.additives],
            non_veg_flags=[NonVegFlagOut(ingredient=f.ingredient, explanation=f.explanation)
                           for f in report.non_veg_flags],
            allergens_detected=report.allergens_detected,
        ),
    )


def _translation_for(product: models.Product, user: models.User) -> List[TranslatedNutrientOut]:
    sodium_limit = user.target_sodium_mg or constants.WHO_SODIUM_LIMIT_MG
    protein_target = user.target_protein_g or constants.DEFAULT_DAILY_TARGETS["protein_g"]
    factor = (product.serving_size_g or 100.0) / 100.0
    t = tr_core.translate(
        sugar_g=product.sugar_g * factor,
        sodium_mg=product.sodium_mg * factor,
        saturated_fat_g=product.saturated_fat_g * factor,
        protein_g=product.protein_g * factor,
        fibre_g=product.fibre_g * factor,
        sodium_limit_mg=sodium_limit,
        protein_target_g=protein_target,
        basis="serving",
    )
    nutrients = [t.sugar, t.sodium, t.saturated_fat, t.protein]
    if t.fibre:
        nutrients.append(t.fibre)
    return [TranslatedNutrientOut(**n.__dict__) for n in nutrients]


def _alternatives_for(
    db: Session, product: models.Product, scanned_stars: float, mode: str,
) -> List[AlternativeOut]:
    pool = product_service.list_by_category(db, product.category, exclude_id=product.id)
    candidates = [_to_candidate(p, _hsr_for(p).stars) for p in pool]
    scanned = _to_candidate(product, scanned_stars)
    ranked = rank_alternatives(scanned, candidates, mode=mode, limit=3)
    return [
        AlternativeOut(
            id=r.candidate.id,
            name=r.candidate.name,
            brand=r.candidate.brand,
            reason=r.reason,
            hsr_stars=r.candidate.hsr_stars,
            price_inr=r.candidate.price_inr,
            image_url=r.candidate.image_url,
        )
        for r in ranked
    ]


def scan(
    db: Session,
    user: models.User,
    barcode: str,
    servings: float,
    log: bool,
    day: Optional[dt.date] = None,
) -> ScanResultOut:
    product = product_service.resolve_product(db, barcode)
    if product is None:
        # Section 11.1 step 3: not found -> prompt for one label photo.
        return ScanResultOut(
            found=False,
            needs_photo=True,
            message="We don't have this one yet. Snap the nutrition label and we'll read it for you.",
        )

    hsr_result = _hsr_for(product)

    if log:
        ledger_service.log_scan(db, user=user, product=product, servings=servings)

    dashboard = ledger_service.build_dashboard(db, user, day=day)

    return ScanResultOut(
        found=True,
        product=ProductOut.model_validate(product),
        headline_nutrient=_headline_key(product),
        translation=_translation_for(product, user),
        alternatives=_alternatives_for(db, product, hsr_result.stars, user.alternatives_priority),
        detail=build_detail_layer(product, hsr_result),
        dashboard=dashboard,
        trust_tier=product.trust_tier,
    )
