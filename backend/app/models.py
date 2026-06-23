"""SQLAlchemy ORM models.

Covers the product catalogue, per-user daily ledger (F3), settings, and the
Section 10 photo-submission / trust-tier data pipeline.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # External auth id (Clerk user id). Internal id stays opaque + random.
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # Settings (single flat screen, PRD 7.2).
    alternatives_priority: Mapped[str] = mapped_column(String(16), default="healthier")
    primary_nutrient: Mapped[str] = mapped_column(String(24), default="sugar")
    # Comma-separated health flags: diabetic,hypertensive,weight_goal
    health_flags: Mapped[str] = mapped_column(String(120), default="")

    # Optional custom daily targets (override defaults).
    target_sugar_tsp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_sodium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    scans: Mapped[list["ScanLog"]] = relationship(back_populates="user")

    @property
    def health_flag_list(self) -> list[str]:
        return [f for f in (self.health_flags or "").split(",") if f]


class Product(Base):
    """A packaged product. Nutrients stored per 100 g / 100 mL (label basis)."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    category: Mapped[str] = mapped_column(String(48), default="general_food", index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)

    # Category flags for HSR classification.
    is_beverage: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dairy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fat_or_oil: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cheese: Mapped[bool] = mapped_column(Boolean, default=False)

    # Nutrients per 100 g / 100 mL.
    energy_kj: Mapped[float] = mapped_column(Float, default=0.0)
    sugar_g: Mapped[float] = mapped_column(Float, default=0.0)
    added_sugar_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0.0)
    saturated_fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    total_fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    fibre_g: Mapped[float] = mapped_column(Float, default=0.0)
    fvnl_percent: Mapped[float] = mapped_column(Float, default=0.0)

    serving_size_g: Mapped[float] = mapped_column(Float, default=100.0)
    price_inr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    front_of_pack_text: Mapped[str] = mapped_column(Text, default="")
    ingredients_text: Mapped[str] = mapped_column(Text, default="")
    declared_veg: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    nova_group: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Section 10 trust tier: verified | confirmed | pending
    trust_tier: Mapped[str] = mapped_column(String(16), default="pending")
    source: Mapped[str] = mapped_column(String(32), default="seed")

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class ScanLog(Base):
    """One logged scan; its contribution to a user-day's ledger (F3)."""

    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    log_date: Mapped[dt.date] = mapped_column(Date, index=True, default=lambda: dt.date.today())
    servings: Mapped[float] = mapped_column(Float, default=1.0)

    # Snapshot of the contribution (in case the product is later corrected).
    sugar_g: Mapped[float] = mapped_column(Float, default=0.0)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0.0)
    saturated_fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    fibre_g: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="scans")
    product: Mapped["Product"] = relationship()


class PhotoSubmission(Base):
    """Section 10: a label photo submitted for a barcode not yet in the DB.

    No user ever types nutrient numbers - only a barcode + a photo. OCR fills
    the values, each with a confidence score; low-confidence fields are gated.
    """

    __tablename__ = "photo_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    image_ref: Mapped[str] = mapped_column(String(400))

    ocr_sugar_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_sodium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_saturated_fat_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_fibre_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_energy_kj: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(String(24), default="received")  # received|ocr_done|gated|matched
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ProductVersion(Base):
    """Section 10.3: version history per barcode - never silently overwritten."""

    __tablename__ = "product_versions"
    __table_args__ = (UniqueConstraint("barcode", "version", name="uq_barcode_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot_json: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(48), default="seed")
    note: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DataReport(Base):
    """Section 10.3: "Report incorrect data" feeding the OCR re-check queue."""

    __tablename__ = "data_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(300), default="")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
