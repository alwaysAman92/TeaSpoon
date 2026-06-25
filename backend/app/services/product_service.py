"""Product catalogue access: DB lookup, OFF fallback, version history."""
from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..schemas import ProductBase
from . import gemini_client, off_client


def get_by_barcode(db: Session, barcode: str) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.barcode == str(barcode)).one_or_none()


def list_by_category(db: Session, category: str, exclude_id: Optional[int] = None) -> List[models.Product]:
    stmt = select(models.Product).where(models.Product.category == category)
    if exclude_id is not None:
        stmt = stmt.where(models.Product.id != exclude_id)
    return list(db.scalars(stmt).all())


def upsert_from_base(
    db: Session,
    data: ProductBase,
    *,
    source: str = "off",
    trust_tier: str = "pending",
    note: str = "",
) -> models.Product:
    """Insert or update a product, recording an immutable version snapshot."""
    existing = get_by_barcode(db, data.barcode)
    payload = data.model_dump()
    payload.pop("source", None)

    if existing is None:
        product = models.Product(**payload, trust_tier=trust_tier, source=source)
        db.add(product)
        db.flush()
        _record_version(db, product, source=source, note=note or "initial")
    else:
        # Never silently overwrite a Verified record from an unverified source.
        if existing.trust_tier == "verified" and source != "manual_verify":
            return existing
        for key, value in payload.items():
            setattr(existing, key, value)
        product = existing
        _record_version(db, product, source=source, note=note or "update")

    db.commit()
    db.refresh(product)
    return product


def _record_version(db: Session, product: models.Product, *, source: str, note: str) -> None:
    last = (
        db.query(models.ProductVersion)
        .filter(models.ProductVersion.barcode == product.barcode)
        .order_by(models.ProductVersion.version.desc())
        .first()
    )
    version = (last.version + 1) if last else 1
    snapshot = {
        "name": product.name,
        "brand": product.brand,
        "sugar_g": product.sugar_g,
        "sodium_mg": product.sodium_mg,
        "saturated_fat_g": product.saturated_fat_g,
        "protein_g": product.protein_g,
        "fibre_g": product.fibre_g,
        "energy_kj": product.energy_kj,
    }
    db.add(models.ProductVersion(
        barcode=product.barcode,
        version=version,
        snapshot_json=json.dumps(snapshot),
        source=source,
        note=note,
    ))


def resolve_product(db: Session, barcode: str) -> Optional[models.Product]:
    """DB first, then Open Food Facts, then Gemini brand-site lookup."""
    product = get_by_barcode(db, barcode)
    if product is not None:
        return product

    off_data = off_client.fetch_product(barcode)
    if off_data is not None:
        return upsert_from_base(db, off_data, source="off", trust_tier="pending", note="off-fetch")

    # NEW: Gemini brand-website fallback
    gemini_data = gemini_client.fetch_from_brand_site(
        product_name=f"product with barcode {barcode}",
        brand=None,
        barcode=barcode,
    )
    if gemini_data is not None:
        return upsert_from_base(
            db,
            gemini_data,
            source="gemini_grounded",
            trust_tier="pending",
            note="gemini-grounded-fetch",
        )

    return None
