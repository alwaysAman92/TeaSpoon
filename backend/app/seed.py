"""Seed the database with real Indian SKUs so a fresh checkout has data.

Run directly:  python -m app.seed
Or it runs automatically on startup if the products table is empty.
"""
from __future__ import annotations

import json
from pathlib import Path

from .database import SessionLocal, init_db
from .models import Product
from .schemas import ProductBase
from .services import product_service

_DATA_FILE = Path(__file__).parent / "data" / "seed_products.json"


def load_seed_products() -> list:
    with open(_DATA_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def seed() -> int:
    init_db()
    db = SessionLocal()
    inserted = 0
    try:
        for raw in load_seed_products():
            trust = raw.pop("trust_tier", "pending")
            data = ProductBase(**raw)
            product_service.upsert_from_base(
                db, data, source="seed", trust_tier=trust, note="seed import"
            )
            inserted += 1
    finally:
        db.close()
    return inserted


def seed_if_empty() -> int:
    db = SessionLocal()
    try:
        count = db.query(Product).count()
    finally:
        db.close()
    if count > 0:
        return 0
    return seed()


if __name__ == "__main__":
    n = seed()
    print(f"Seeded {n} products into the catalogue.")
