from app.core import constants, translation


def test_sugar_to_tsp():
    assert translation.grams_sugar_to_tsp(40) == 10.0
    assert translation.grams_sugar_to_tsp(18) == 4.5
    assert translation.grams_sugar_to_tsp(0) == 0.0


def test_negative_values_clamped():
    assert translation.grams_sugar_to_tsp(-5) == 0.0
    assert translation.sodium_mg_to_pct_limit(-100) == 0.0


def test_sodium_pct_of_who_limit():
    assert translation.sodium_mg_to_pct_limit(2000) == 100.0
    assert translation.sodium_mg_to_pct_limit(1200) == 60.0


def test_fat_to_tsp():
    assert translation.grams_fat_to_tsp(4.5) == 1.0
    assert translation.grams_fat_to_tsp(9) == 2.0


def test_salt_to_sodium():
    # 5 g salt -> 2000 mg sodium
    assert round(translation.salt_to_sodium_mg(5.0)) == 2000


def test_translate_headlines():
    t = translation.translate(
        sugar_g=18, sodium_mg=1200, saturated_fat_g=4.5, protein_g=8, fibre_g=3,
    )
    assert t.sugar.headline == "4.5 tsp of sugar"
    assert t.sugar.plain_value == 4.5
    assert t.sodium.plain_value == 60.0
    assert t.saturated_fat.plain_value == 1.0
    assert "8g of 70g protein" in t.protein.headline
    assert t.fibre is not None and t.fibre.raw_value == 3


def test_custom_protein_target():
    t = translation.translate(
        sugar_g=0, sodium_mg=0, saturated_fat_g=0, protein_g=20,
        protein_target_g=50,
    )
    assert "20g of 50g protein" in t.protein.headline


def test_default_targets_match_prd_dashboard():
    assert constants.DEFAULT_DAILY_TARGETS["sugar_tsp"] == 10.0
    assert constants.DEFAULT_DAILY_TARGETS["protein_g"] == 70.0
