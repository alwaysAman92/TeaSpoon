import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.core.serving_helper import needs_serving_input, get_serving_presets
from app.services import scan_service, product_service
from app.schemas import ProductBase


@pytest.fixture(scope="module")
def test_engine():
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


def test_needs_serving_input_categories():
    # Spreads, jams, oils, sauces keywords -> True
    assert needs_serving_input("Peanut Butter") is True
    assert needs_serving_input("Strawberry Jam") is True
    assert needs_serving_input("Olive Oil") is True
    assert needs_serving_input("Ghee") is True
    assert needs_serving_input("Tomato Sauce") is True
    assert needs_serving_input("Soy Sauce") is True
    assert needs_serving_input("Mayonnaise") is True

    # Beverages, snacks -> False
    assert needs_serving_input("Coca-Cola Soda") is False
    assert needs_serving_input("Potato Chips") is False
    assert needs_serving_input("Cheddar Cheese") is False
    assert needs_serving_input("Whole Milk") is False


def test_get_serving_presets():
    presets = get_serving_presets("Peanut Butter")
    assert len(presets) == 3
    assert presets[0] == {"label": "1 tsp", "grams": 5.0}
    assert presets[1] == {"label": "1 tbsp", "grams": 15.0}
    assert presets[2] == {"label": "2 tbsp", "grams": 30.0}


def test_scan_variable_serving_returns_presets(db):
    # Setup user and variable-serving product
    user = models.User(external_id="test-serving-user", points=0)
    db.add(user)
    db.commit()

    product_data = ProductBase(
        barcode="8901234554321",
        name="Organic Peanut Butter",
        brand="BrandName",
        category="general_food",
        needs_serving_input=True,
        sugar_g=10.0,
        sodium_mg=200.0,
        saturated_fat_g=4.0,
        protein_g=25.0,
        serving_size_g=100.0,
    )
    product = product_service.upsert_from_base(db, product_data, source="test", trust_tier="verified")

    # Perform preview (log=False, servings=1.0)
    res = scan_service.scan(db, user, "8901234554321", servings=1.0, log=False)

    assert res.found is True
    assert res.needs_serving_input is True
    assert len(res.serving_presets) == 3
    assert res.serving_presets[1] == {"label": "1 tbsp", "grams": 15.0}


def test_log_scan_scaled_nutrient_math(db):
    user = db.query(models.User).filter(models.User.external_id == "test-serving-user").one()
    # A product with 6g sugar per 100g, logged at a chosen 15g serving, should translate based on 0.9g of sugar.
    # serving_size_g = 100g, chosen_serving = 15g, servings multiplier = 15 / 100 = 0.15.
    product_data = ProductBase(
        barcode="8906000000001",
        name="Tomato Ketchup",
        brand="KetchupBrand",
        category="general_food",
        needs_serving_input=True,
        sugar_g=6.0,      # 6g per 100g
        sodium_mg=1000.0,
        saturated_fat_g=0.0,
        protein_g=1.0,
        serving_size_g=100.0,
    )
    product = product_service.upsert_from_base(db, product_data, source="test", trust_tier="verified")

    # Log scan with servings=0.15 (15g serving size)
    res = scan_service.scan(db, user, "8906000000001", servings=0.15, log=True)

    assert res.found is True

    # Assert scaled sugar is translated:
    # 6g * 0.15 = 0.9g. Since sugar_g * factor is 0.9g, sugar in teaspoons is 0.9 / 4 = 0.225 tsp.
    # The translation module rounds plain_value to 1 decimal place, so 0.225 rounds to 0.2.
    sugar_translation = next(t for t in res.translation if t.key == "sugar")
    assert sugar_translation.plain_unit == "tsp"
    assert sugar_translation.plain_value == 0.2
    assert sugar_translation.raw_value == 0.9


def test_fixed_serving_product_no_change(db):
    user = db.query(models.User).filter(models.User.external_id == "test-serving-user").one()
    # A beverage product should not show needs_serving_input=True
    product_data = ProductBase(
        barcode="8901058002345",
        name="Mango Juice Drink",
        brand="Juicy",
        category="beverages",
        needs_serving_input=False,
        sugar_g=12.0,
        sodium_mg=10.0,
        saturated_fat_g=0.0,
        protein_g=0.2,
        serving_size_g=250.0,
    )
    product = product_service.upsert_from_base(db, product_data, source="test", trust_tier="verified")

    res = scan_service.scan(db, user, "8901058002345", servings=1.0, log=False)

    assert res.found is True
    assert res.needs_serving_input is False
    assert len(res.serving_presets) == 0
