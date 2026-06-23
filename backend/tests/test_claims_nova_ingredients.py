from app.core.claims import ClaimsInput, detect_claims
from app.core.ingredients import analyse_ingredients
from app.core.nova import classify_nova


def test_high_protein_claim_honest():
    res = detect_claims(ClaimsInput(
        front_of_pack_text="High Protein Bar", sugar_g=5, sodium_mg=100,
        protein_g=20, saturated_fat_g=2,
    ))
    assert not res.has_misleading


def test_high_protein_claim_misleading():
    res = detect_claims(ClaimsInput(
        front_of_pack_text="HIGH PROTEIN", sugar_g=30, sodium_mg=100,
        protein_g=4, saturated_fat_g=2,
    ))
    assert res.has_misleading
    assert res.badge == "Marketing vs Reality"


def test_no_added_sugar_caught_by_ingredient():
    res = detect_claims(ClaimsInput(
        front_of_pack_text="No Added Sugar", sugar_g=20, sodium_mg=50,
        protein_g=2, saturated_fat_g=1,
        ingredients_text="oats, glucose syrup, salt",
    ))
    assert res.has_misleading


def test_multigrain_with_maida_is_misleading():
    res = detect_claims(ClaimsInput(
        front_of_pack_text="Multigrain Biscuit", sugar_g=20, sodium_mg=300,
        protein_g=6, saturated_fat_g=5, fibre_g=2,
        ingredients_text="refined wheat flour (maida), sugar, edible oil",
    ))
    assert res.has_misleading


def test_no_added_msg_with_621():
    res = detect_claims(ClaimsInput(
        front_of_pack_text="No Added MSG", sugar_g=2, sodium_mg=900,
        protein_g=8, saturated_fat_g=10,
        ingredients_text="wheat flour, palm oil, salt, flavour enhancer (ins 621)",
    ))
    assert res.has_misleading


def test_nova_detects_ultra_processed():
    r = classify_nova(ingredients_text="water, sugar, acidity regulator (ins 330), aspartame, flavouring")
    assert r.group == 4


def test_nova_zero_sugar_soda_still_group4():
    r = classify_nova(ingredients_text="carbonated water, sweetener (sucralose), colour, preservative")
    assert r.group == 4


def test_nova_whole_food():
    r = classify_nova(ingredients_text="rolled oats")
    assert r.group in (1, 2)


def test_off_nova_group_preferred():
    r = classify_nova(ingredients_text="rolled oats", off_nova_group=3)
    assert r.group == 3


def test_ingredients_flags_gelatin():
    report = analyse_ingredients("sugar, gelatin, citric acid (ins 330), colour (ins 120)")
    assert report.veg_status == "non_veg"
    assert any("gelatin" in f.ingredient for f in report.non_veg_flags)
    codes = {a.code for a in report.additives}
    assert "330" in codes and "120" in codes


def test_ingredients_ambiguous_additive():
    report = analyse_ingredients("wheat flour, emulsifier (ins 471)")
    assert report.veg_status == "uncertain"
