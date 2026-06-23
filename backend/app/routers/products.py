"""Product catalogue + Section 10 data-integrity endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..schemas import DataReportRequest, ProductOut
from ..services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{barcode}", response_model=ProductOut)
def get_product(barcode: str, db: Session = Depends(get_db)) -> ProductOut:
    product = product_service.resolve_product(db, barcode)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut.model_validate(product)


@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[ProductOut]:
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.category == category)
    return [ProductOut.model_validate(p) for p in query.limit(200).all()]


@router.post("/report", status_code=201)
def report_incorrect_data(
    payload: DataReportRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    """Section 10.3: "Report incorrect data" -> OCR re-check queue."""
    report = models.DataReport(barcode=payload.barcode, user_id=user.id, reason=payload.reason)
    db.add(report)
    db.commit()
    return {"status": "queued", "barcode": payload.barcode}


@router.get("/{barcode}/history")
def product_history(barcode: str, db: Session = Depends(get_db)) -> List[dict]:
    """Section 10.3: version history per barcode (enables Reformulation Watch)."""
    versions = (
        db.query(models.ProductVersion)
        .filter(models.ProductVersion.barcode == barcode)
        .order_by(models.ProductVersion.version.desc())
        .all()
    )
    return [
        {
            "version": v.version,
            "source": v.source,
            "note": v.note,
            "snapshot": v.snapshot_json,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
