from app.core.hsr import (
    HSRCategory,
    HSRInput,
    calculate_hsr,
    classify_category,
)


def test_healthy_food_scores_high():
    # Plain rolled oats: low sat-fat/sugar/sodium, decent protein + fibre.
    oats = HSRInput(
        energy_kj=1500, saturated_fat_g=1.3, total_sugars_g=1.0,
        sodium_mg=5, protein_g=13, fibre_g=10, fvnl_percent=0,
    )
    result = calculate_hsr(oats, HSRCategory.FOOD)
    assert result.stars >= 4.0


def test_junk_food_scores_low():
    # Sugary, salty, fatty biscuit.
    biscuit = HSRInput(
        energy_kj=2100, saturated_fat_g=12, total_sugars_g=35,
        sodium_mg=450, protein_g=6, fibre_g=2, fvnl_percent=0,
    )
    result = calculate_hsr(biscuit, HSRCategory.FOOD)
    assert result.stars <= 2.5


def test_protein_gating_blocks_offset_on_unhealthy_product():
    # Very unhealthy product (baseline >= 13) with no FVNL: protein must NOT count.
    junk = HSRInput(
        energy_kj=3400, saturated_fat_g=14, total_sugars_g=46,
        sodium_mg=950, protein_g=25, fibre_g=0, fvnl_percent=0,
    )
    result = calculate_hsr(junk, HSRCategory.FOOD)
    assert result.baseline_points >= 13
    assert result.protein_counted is False
    assert result.protein_points > 0  # protein exists ...
    # ... but does not reduce the final score
    assert result.modifying_points == result.fvnl_points + result.fibre_points


def test_protein_counts_when_baseline_low():
    lean = HSRInput(
        energy_kj=500, saturated_fat_g=1, total_sugars_g=2,
        sodium_mg=50, protein_g=20, fibre_g=1, fvnl_percent=0,
    )
    result = calculate_hsr(lean, HSRCategory.FOOD)
    assert result.baseline_points < 13
    assert result.protein_counted is True


def test_beverage_uses_beverage_sugar_table():
    soda = HSRInput(
        energy_kj=180, saturated_fat_g=0, total_sugars_g=11,
        sodium_mg=10, protein_g=0, fibre_g=0, fvnl_percent=0,
    )
    result = calculate_hsr(soda, HSRCategory.BEVERAGE)
    assert result.category == HSRCategory.BEVERAGE
    assert result.stars <= 3.5


def test_classify_category():
    assert classify_category(is_beverage=True) == HSRCategory.BEVERAGE
    assert classify_category(is_beverage=True, is_dairy=True) == HSRCategory.DAIRY_BEVERAGE
    assert classify_category(is_beverage=False, is_cheese=True) == HSRCategory.CHEESE
    assert classify_category(is_beverage=False, is_fat_or_oil=True) == HSRCategory.FATS_OILS
    assert classify_category(is_beverage=False) == HSRCategory.FOOD


def test_stars_are_in_valid_range():
    for sugar in range(0, 60, 5):
        r = calculate_hsr(
            HSRInput(energy_kj=1000, saturated_fat_g=2, total_sugars_g=sugar,
                     sodium_mg=200, protein_g=5, fibre_g=2),
            HSRCategory.FOOD,
        )
        assert 0.5 <= r.stars <= 5.0
        assert (r.stars * 2) == int(r.stars * 2)  # half-star steps
