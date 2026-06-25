from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.schemas import ProductBase
from app.services import gemini_client, product_service
from app.services.gemini_client import GeminiResponseSchema


@pytest.fixture(scope="module")
def test_engine():
    # Use an isolated, clean in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_fetch_from_brand_site_success():
    # 1. Model returns a complete, valid JSON with found: true and all four required fields populated
    # -> returns a populated ProductBase with source="gemini_grounded" and the correct source_url.
    mock_parsed = GeminiResponseSchema(
        found=True,
        source_url="https://brandsite.com/product",
        product_name="Brand Super Cookies",
        brand="BrandName",
        energy_kj=1200.0,
        sugar_g=15.0,
        sodium_mg=150.0,
        saturated_fat_g=5.0,
        protein_g=6.0,
        fibre_g=2.0,
        total_fat_g=10.0,
        ingredients_text="Flour, sugar, chocolate chips",
        is_beverage=False,
        is_dairy=False,
        is_fat_or_oil=False,
        is_cheese=False,
    )

    with patch("app.services.gemini_client.genai.Client") as mock_client_cls, \
         patch("app.services.gemini_client.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = mock_parsed
        mock_client.models.generate_content.return_value = mock_response

        res = gemini_client.fetch_from_brand_site("Super Cookies", "BrandName", "123456789")

        assert res is not None
        assert isinstance(res, ProductBase)
        assert res.barcode == "123456789"
        assert res.name == "Brand Super Cookies"
        assert res.brand == "BrandName"
        assert res.source == "gemini_grounded"
        assert res.source_url == "https://brandsite.com/product"
        assert res.sugar_g == 15.0
        assert res.sodium_mg == 150.0
        assert res.saturated_fat_g == 5.0
        assert res.protein_g == 6.0
        assert res.total_fat_g == 10.0
        assert res.ingredients_text == "Flour, sugar, chocolate chips"


def test_fetch_from_brand_site_not_found():
    # 2. Model returns found: false -> returns None.
    mock_parsed = GeminiResponseSchema(
        found=False
    )
    with patch("app.services.gemini_client.genai.Client") as mock_client_cls, \
         patch("app.services.gemini_client.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = mock_parsed
        mock_client.models.generate_content.return_value = mock_response

        res = gemini_client.fetch_from_brand_site("Super Cookies", "BrandName", "123456789")
        assert res is None


def test_fetch_from_brand_site_missing_required_fields():
    # 3. Model returns found: true but one of the four required fields is null -> returns None.
    required_fields = ["sugar_g", "sodium_mg", "saturated_fat_g", "protein_g"]
    for field in required_fields:
        kwargs = {
            "found": True,
            "source_url": "https://brandsite.com/product",
            "product_name": "Brand Super Cookies",
            "brand": "BrandName",
            "sugar_g": 15.0,
            "sodium_mg": 150.0,
            "saturated_fat_g": 5.0,
            "protein_g": 6.0,
        }
        kwargs[field] = None  # force one to be null
        mock_parsed = GeminiResponseSchema(**kwargs)

        with patch("app.services.gemini_client.genai.Client") as mock_client_cls, \
             patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.gemini_api_key = "fake-key"
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_response.parsed = mock_parsed
            mock_client.models.generate_content.return_value = mock_response

            res = gemini_client.fetch_from_brand_site("Super Cookies", "BrandName", "123456789")
            assert res is None, f"Expected None when {field} is null"


def test_fetch_from_brand_site_malformed_json():
    # 4. Model returns malformed/unparseable JSON (mocking parsed as None) -> returns None.
    with patch("app.services.gemini_client.genai.Client") as mock_client_cls, \
         patch("app.services.gemini_client.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = None
        mock_client.models.generate_content.return_value = mock_response

        res = gemini_client.fetch_from_brand_site("Super Cookies", "BrandName", "123456789")
        assert res is None


def test_fetch_from_brand_site_exception():
    # 5. The underlying API call raises an exception -> returns None.
    with patch("app.services.gemini_client.genai.Client") as mock_client_cls, \
         patch("app.services.gemini_client.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_client.models.generate_content.side_effect = Exception("API connection timeout")

        res = gemini_client.fetch_from_brand_site("Super Cookies", "BrandName", "123456789")
        assert res is None


def test_resolve_product_fallback_to_gemini(db):
    # Confirming the full chain: when both DB and OFF return nothing,
    # but Gemini returns valid data, the product gets created with
    # source="gemini_grounded" and trust_tier="pending".
    barcode = "9998887776665"

    # Ensure product is not in database
    existing = db.query(models.Product).filter(models.Product.barcode == barcode).one_or_none()
    if existing:
        db.delete(existing)
        db.commit()

    mock_parsed = GeminiResponseSchema(
        found=True,
        source_url="https://brandsite.com/gemini-product",
        product_name="Gemini Grounded Product",
        brand="Gemini Brand",
        energy_kj=500.0,
        sugar_g=10.0,
        sodium_mg=50.0,
        saturated_fat_g=2.0,
        protein_g=3.0,
        fibre_g=1.0,
        total_fat_g=4.0,
        ingredients_text="Oats, honey",
        is_beverage=False,
        is_dairy=False,
        is_fat_or_oil=False,
        is_cheese=False,
    )

    with patch("app.services.off_client.fetch_product", return_value=None), \
         patch("app.services.gemini_client.genai.Client") as mock_client_cls, \
         patch("app.services.gemini_client.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = mock_parsed
        mock_client.models.generate_content.return_value = mock_response

        product = product_service.resolve_product(db, barcode)

        assert product is not None
        assert product.barcode == barcode
        assert product.name == "Gemini Grounded Product"
        assert product.source == "gemini_grounded"
        assert product.source_url == "https://brandsite.com/gemini-product"
        assert product.trust_tier == "pending"

        # Verify it was saved in the database
        db_product = db.query(models.Product).filter(models.Product.barcode == barcode).one_or_none()
        assert db_product is not None
        assert db_product.source == "gemini_grounded"
        assert db_product.source_url == "https://brandsite.com/gemini-product"
        assert db_product.trust_tier == "pending"
