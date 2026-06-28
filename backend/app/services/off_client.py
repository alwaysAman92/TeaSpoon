"""Open Food Facts client (PRD Section 11.1, step 2).

Falls back to the OFF API when a barcode is not in our own catalogue. OFF data
is licensed CC BY-SA. We only read; we never write user data here.
"""
from __future__ import annotations

from typing import Optional

import httpx

from ..config import get_settings
from ..core.serving_helper import needs_serving_input
from ..schemas import ProductBase

settings = get_settings()

_BEVERAGE_HINTS = ("beverages", "drinks", "sodas", "juices", "waters", "milks")
_DAIRY_HINTS = ("dairy", "milk", "yogurt", "yoghurt", "curd")
_FAT_HINTS = ("oils", "fats", "ghee", "butters", "spreads", "margarine")
_CHEESE_HINTS = ("cheese", "cheeses")


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category(tags: list) -> tuple:
    joined = " ".join(tags).lower()
    is_beverage = any(h in joined for h in _BEVERAGE_HINTS)
    is_dairy = any(h in joined for h in _DAIRY_HINTS)
    is_fat = any(h in joined for h in _FAT_HINTS)
    is_cheese = any(h in joined for h in _CHEESE_HINTS)
    return is_beverage, is_dairy, is_fat, is_cheese


def _category_key(is_beverage, is_dairy, is_fat, is_cheese) -> str:
    if is_cheese:
        return "cheese"
    if is_fat:
        return "fats_oils"
    if is_beverage:
        return "dairy_beverages" if is_dairy else "beverages"
    return "dairy_food" if is_dairy else "general_food"


def fetch_product(barcode: str) -> Optional[ProductBase]:
    """Look up a barcode on Open Food Facts. Returns None if not found."""
    url = f"{settings.off_base_url}/api/v2/product/{barcode}.json"
    headers = {"User-Agent": settings.off_user_agent}
    try:
        resp = httpx.get(url, headers=headers, timeout=settings.off_timeout_seconds)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None

    payload = resp.json()
    # Return None if the API indicates failure or if no product data is present.
    if payload.get("status") != 1:
        return None
    if not payload.get("product"):
        return None

    p = payload.get("product", {})
    nutr = p.get("nutriments", {}) or {}

    # Required fields check: treat the product as not-found if essential nutrients are missing
    if (
        nutr.get("sugars_100g") is None
        or nutr.get("proteins_100g") is None
        or nutr.get("saturated-fat_100g") is None
        or (nutr.get("sodium_100g") is None and nutr.get("salt_100g") is None)
    ):
        return None

    tags = p.get("categories_tags", []) or []
    is_beverage, is_dairy, is_fat, is_cheese = _category(tags)

    # OFF sodium is in g/100g; convert to mg. Prefer sodium, fall back to salt.
    sodium_mg = _num(nutr.get("sodium_100g")) * 1000.0
    if sodium_mg <= 0 and nutr.get("salt_100g") is not None:
        sodium_mg = _num(nutr.get("salt_100g")) / 2.5 * 1000.0

    energy_kj = _num(nutr.get("energy-kj_100g"))
    if energy_kj <= 0 and nutr.get("energy-kcal_100g") is not None:
        energy_kj = _num(nutr.get("energy-kcal_100g")) * 4.184

    veg_tags = " ".join(tags).lower()
    declared_veg = None
    if "vegan" in veg_tags or "vegetarian" in veg_tags:
        declared_veg = True
    elif "non-vegetarian" in veg_tags or "meat" in veg_tags:
        declared_veg = False

    product_name_str = p.get("product_name") or p.get("generic_name") or ""
    serving_input_needed = needs_serving_input(product_name_str, tags)

    return ProductBase(
        barcode=str(barcode),
        name=product_name_str or f"Product {barcode}",
        brand=(p.get("brands") or "").split(",")[0].strip() or None,
        category=_category_key(is_beverage, is_dairy, is_fat, is_cheese),
        image_url=p.get("image_front_url") or p.get("image_url"),
        needs_serving_input=serving_input_needed,
        is_beverage=is_beverage,
        is_dairy=is_dairy,
        is_fat_or_oil=is_fat,
        is_cheese=is_cheese,
        energy_kj=energy_kj,
        sugar_g=_num(nutr.get("sugars_100g")),
        sodium_mg=sodium_mg,
        saturated_fat_g=_num(nutr.get("saturated-fat_100g")),
        total_fat_g=_num(nutr.get("fat_100g")),
        protein_g=_num(nutr.get("proteins_100g")),
        fibre_g=_num(nutr.get("fiber_100g")),
        fvnl_percent=_num(nutr.get("fruits-vegetables-nuts-estimate-from-ingredients_100g")),
        serving_size_g=_num(p.get("serving_quantity"), 100.0) or 100.0,
        package_weight_g=_num(p.get("product_quantity"), None),
        front_of_pack_text=p.get("product_name") or "",
        ingredients_text=p.get("ingredients_text") or "",
        declared_veg=declared_veg,
        nova_group=int(p["nova_group"]) if str(p.get("nova_group", "")).isdigit() else None,
    )
