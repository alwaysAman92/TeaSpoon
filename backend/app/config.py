"""Application configuration, loaded from environment variables.

Secrets are never hard-coded (DB URL, OCR keys, Clerk keys come from the
environment / a secrets manager). Sensible local defaults let the app boot on
SQLite with zero setup; production overrides point at PostgreSQL + Redis.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.app_name: str = "TeaSpoon API"
        self.version: str = "5.0.0"
        self.environment: str = os.getenv("TEASPOON_ENV", "development")

        # SQLite by default so the API runs with no external services.
        # In production set DATABASE_URL to a PostgreSQL DSN.
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./teaspoon.db"
        )

        # Open Food Facts (no key required; identify ourselves politely).
        self.off_base_url: str = os.getenv(
            "OFF_BASE_URL", "https://world.openfoodfacts.org"
        )
        self.off_user_agent: str = os.getenv(
            "OFF_USER_AGENT", "TeaSpoon/5.0 (https://teaspoon.app)"
        )
        self.off_timeout_seconds: float = float(os.getenv("OFF_TIMEOUT", "6"))

        # OCR + auth provider keys come from the environment only.
        self.gcv_api_key: str = os.getenv("GOOGLE_CLOUD_VISION_API_KEY", "")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.clerk_secret_key: str = os.getenv("CLERK_SECRET_KEY", "")

        # CORS - allow the local Expo dev server and the landing page origin.
        self.cors_origins: List[str] = _split(
            os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:8081,http://localhost:8082,http://localhost:8083,http://localhost:8084,http://localhost:8085,http://localhost:19006,http://localhost:5173")
        )

        # OCR confidence below which a field is held back from going live.
        self.ocr_min_confidence: float = float(os.getenv("OCR_MIN_CONFIDENCE", "0.6"))


def _split(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
