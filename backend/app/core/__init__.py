"""TeaSpoon core logic - deterministic, testable, auditable maths (PRD Phase 0).

Pure Python with no I/O or framework dependencies so it can be unit-tested in
isolation and reused by the FastAPI layer.
"""
from . import (
    alternatives,
    claims,
    constants,
    hsr,
    ingredients,
    ledger,
    nova,
    translation,
)

__all__ = [
    "alternatives",
    "claims",
    "constants",
    "hsr",
    "ingredients",
    "ledger",
    "nova",
    "translation",
]
