"""Gemini-grounded brand-website lookup (PRD Section 10, fallback step 3).

Used only when a barcode is in neither our own database nor Open Food
Facts. Asks Gemini, with Google Search grounding enabled, to find the
official nutrition facts for a named product on the brand's own website.
Returns None if Gemini cannot find a confident, citable answer -- this
function must NEVER return guessed or estimated values.
"""
from __future__ import annotations

import logging
from typing import Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

from ..config import get_settings
from ..core.serving_helper import needs_serving_input
from ..schemas import ProductBase

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiResponseSchema(BaseModel):
    found: bool
    source_url: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    energy_kj: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    protein_g: Optional[float] = None
    fibre_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    ingredients_text: Optional[str] = None
    is_beverage: Optional[bool] = None
    is_dairy: Optional[bool] = None
    is_fat_or_oil: Optional[bool] = None
    is_cheese: Optional[bool] = None


def _category_key(is_beverage: bool, is_dairy: bool, is_fat: bool, is_cheese: bool) -> str:
    if is_cheese:
        return "cheese"
    if is_fat:
        return "fats_oils"
    if is_beverage:
        return "dairy_beverages" if is_dairy else "beverages"
    return "dairy_food" if is_dairy else "general_food"


def fetch_from_brand_site(
    product_name: str,
    brand: Optional[str],
    barcode: str,
) -> Optional[ProductBase]:
    if not settings.gemini_api_key:
        logger.warning("Gemini API key is not configured.")
        return None

    # Determine if this is a barcode-only fallback search.
    is_barcode_only = False
    if not product_name or f"barcode {barcode}" in product_name.lower():
        is_barcode_only = True

    if is_barcode_only:
        prompt = (
            f"Identify the product with barcode '{barcode}'. "
            "Use Google Search to first determine the official product name and brand. "
            "If you cannot confidently identify a single product name and brand for this barcode, "
            "or if search results are conflicting or ambiguous, you must return found=false. "
            "Once identified, search the brand's official website for official nutrition facts."
        )
    else:
        brand_str = f" by brand '{brand}'" if brand else ""
        prompt = (
            f"Find the official nutrition facts for '{product_name}'{brand_str} (barcode: '{barcode}'). "
            "Use Google Search to locate the product on the official brand website."
        )

    prompt += (
        "\n\nInstructions:\n"
        "1. You MUST find the nutrition facts on the official brand website (e.g. manufacturer's own product page). "
        "DO NOT use third-party online retailers (Amazon, BigBasket, Flipkart, etc.), blogs, reviews, or unverified crowd-sourced sites.\n"
        "2. If the nutrition facts are not present on the official brand website, or if you are not 100% confident "
        "in the values, you must return found=false.\n"
        "3. NEVER guess, estimate, or fill in plausible-sounding numbers. If a specific nutrient is not listed "
        "or you are not sure about it, set that field to null. DO NOT guess it.\n"
        "4. Nutrition facts MUST be converted to per 100g or per 100ml. If the official website lists them per serving, "
        "use the serving size to calculate the values per 100g/100ml and show your source URL in source_url.\n"
        "5. For the required fields: sugar_g, sodium_mg, saturated_fat_g, and protein_g. You MUST be confident about "
        "ALL of these four fields and they must be non-null to return found=true. If any of these four fields "
        "is null, missing, or estimated, you must return found=false."
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="application/json",
            response_schema=GeminiResponseSchema,
        )
        # We use gemini-2.0-flash as the standard default model for this task.
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        )

        if not response or not response.parsed:
            logger.warning("Gemini returned empty or unparseable response.")
            return None

        data: GeminiResponseSchema = response.parsed

        if not data.found:
            return None

        # Verify the four required fields are populated.
        if (
            data.sugar_g is None
            or data.sodium_mg is None
            or data.saturated_fat_g is None
            or data.protein_g is None
        ):
            logger.warning(
                "Gemini returned found=true but one of the four required nutrient fields was null."
            )
            return None

        # Clean/fallback name & brand.
        final_name = data.product_name or product_name
        if not final_name or f"barcode {barcode}" in final_name.lower():
            final_name = f"Product {barcode}"

        final_brand = data.brand or brand or None

        is_bev = bool(data.is_beverage)
        is_dry = bool(data.is_dairy)
        is_fat = bool(data.is_fat_or_oil)
        is_chs = bool(data.is_cheese)

        category = _category_key(is_bev, is_dry, is_fat, is_chs)
        serving_input_needed = needs_serving_input(final_name, category=category)

        return ProductBase(
            barcode=str(barcode),
            name=final_name,
            brand=final_brand,
            category=category,
            image_url=None,
            source="gemini_grounded",
            source_url=data.source_url,
            needs_serving_input=serving_input_needed,
            is_beverage=is_bev,
            is_dairy=is_dry,
            is_fat_or_oil=is_fat,
            is_cheese=is_chs,
            energy_kj=data.energy_kj or 0.0,
            sugar_g=data.sugar_g,
            sodium_mg=data.sodium_mg,
            saturated_fat_g=data.saturated_fat_g,
            total_fat_g=data.total_fat_g or 0.0,
            protein_g=data.protein_g,
            fibre_g=data.fibre_g or 0.0,
            fvnl_percent=0.0,
            serving_size_g=100.0,
            front_of_pack_text=final_name,
            ingredients_text=data.ingredients_text or "",
            declared_veg=None,
            nova_group=None,
        )

    except Exception as e:
        logger.error(f"Error fetching product from brand site via Gemini: {e}", exc_info=True)
        return None
