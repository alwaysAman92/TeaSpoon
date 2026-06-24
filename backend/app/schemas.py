"""Pydantic request/response models (the API contract)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Products ---------------------------------------------------------------

class ProductBase(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    category: str = "general_food"
    image_url: Optional[str] = None

    is_beverage: bool = False
    is_dairy: bool = False
    is_fat_or_oil: bool = False
    is_cheese: bool = False

    energy_kj: float = 0.0
    sugar_g: float = 0.0
    added_sugar_g: Optional[float] = None
    sodium_mg: float = 0.0
    saturated_fat_g: float = 0.0
    total_fat_g: float = 0.0
    protein_g: float = 0.0
    fibre_g: float = 0.0
    fvnl_percent: float = 0.0

    serving_size_g: float = 100.0
    price_inr: Optional[float] = None
    front_of_pack_text: str = ""
    ingredients_text: str = ""
    declared_veg: Optional[bool] = None
    nova_group: Optional[int] = None


class ProductOut(ProductBase):
    id: int
    trust_tier: str

    model_config = ConfigDict(from_attributes=True)


# --- Translation / result card ---------------------------------------------

class TranslatedNutrientOut(BaseModel):
    key: str
    label: str
    raw_value: float
    raw_unit: str
    plain_value: float
    plain_unit: str
    headline: str


class AlternativeOut(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    reason: str
    hsr_stars: float
    price_inr: Optional[float] = None
    image_url: Optional[str] = None


class HSROut(BaseModel):
    stars: float
    final_score: int
    baseline_points: int
    modifying_points: int
    protein_counted: bool


class NovaOut(BaseModel):
    group: int
    label: str
    tag: str
    rationale: str


class ClaimOut(BaseModel):
    claim: str
    verdict: str
    explanation: str


class ClaimsOut(BaseModel):
    badge: Optional[str]
    findings: List[ClaimOut]


class AdditiveOut(BaseModel):
    code: str
    plain_english: str
    possibly_non_veg: bool


class NonVegFlagOut(BaseModel):
    ingredient: str
    explanation: str


class IngredientsOut(BaseModel):
    veg_status: str
    note: str
    additives: List[AdditiveOut]
    non_veg_flags: List[NonVegFlagOut]
    allergens_detected: List[str] = Field(default_factory=list)


class DetailLayerOut(BaseModel):
    """F6-F9: the tap-for-details layer, collapsed by default in the UI."""

    hsr: HSROut
    nova: NovaOut
    claims: ClaimsOut
    ingredients: IngredientsOut


class NutrientProgressOut(BaseModel):
    key: str
    label: str
    consumed: float
    target: float
    unit: str
    pct: float
    is_goal: bool
    headline: str


class RecentScanOut(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    category: str
    image_url: Optional[str] = None
    logged_at: str
    sugar_tsp: float
    sodium_mg: float
    protein_g: float


class DashboardOut(BaseModel):
    date: str
    primary: NutrientProgressOut
    secondary: List[NutrientProgressOut]
    takeaway: str
    scans_today: int
    streak: int = 0
    recent: List[RecentScanOut] = Field(default_factory=list)


class ScanResultOut(BaseModel):
    """The full result card payload returned from POST /scan."""

    found: bool
    product: Optional[ProductOut] = None
    headline_nutrient: Optional[str] = None
    translation: List[TranslatedNutrientOut] = Field(default_factory=list)
    alternatives: List[AlternativeOut] = Field(default_factory=list)
    detail: Optional[DetailLayerOut] = None
    dashboard: Optional[DashboardOut] = None
    trust_tier: Optional[str] = None
    needs_photo: bool = False
    message: Optional[str] = None


# --- Requests ---------------------------------------------------------------

class ScanRequest(BaseModel):
    barcode: str
    servings: float = 1.0
    log: bool = True  # add to the daily ledger


class ManualEntryRequest(BaseModel):
    barcode: str = Field(..., min_length=6, max_length=20)


class SettingsUpdate(BaseModel):
    alternatives_priority: Optional[str] = Field(None, pattern="^(healthier|cheaper)$")
    primary_nutrient: Optional[str] = None
    health_flags: Optional[List[str]] = None
    target_sugar_tsp: Optional[float] = None
    target_sodium_mg: Optional[float] = None
    target_protein_g: Optional[float] = None
    city: Optional[str] = None
    region: Optional[str] = None


class SettingsOut(BaseModel):
    alternatives_priority: str
    primary_nutrient: str
    health_flags: List[str]
    target_sugar_tsp: Optional[float]
    target_sodium_mg: Optional[float]
    target_protein_g: Optional[float]
    points: int = 0
    city: Optional[str] = None
    region: Optional[str] = None
    badges: List[str] = Field(default_factory=list)


class DataReportRequest(BaseModel):
    barcode: str
    reason: str = ""
