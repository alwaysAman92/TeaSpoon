from app.services.ocr_service import parse_nutrition_text

LABEL = """
Nutritional Information (per 100 g)
Energy 480 kcal
Protein 7.0 g
Total Fat 18.0 g
  Saturated Fat 8.0 g
Total Sugars 24.0 g
  Added Sugars 20.0 g
Dietary Fibre 2.0 g
Sodium 320 mg
"""


def test_parses_core_fields():
    fields = parse_nutrition_text(LABEL)
    assert round(fields["protein_g"].value, 1) == 7.0
    assert round(fields["sugar_g"].value, 1) == 24.0
    assert round(fields["saturated_fat_g"].value, 1) == 8.0
    assert round(fields["sodium_mg"].value, 0) == 320
    assert round(fields["fibre_g"].value, 1) == 2.0


def test_energy_kcal_converted_to_kj():
    fields = parse_nutrition_text(LABEL)
    assert round(fields["energy_kj"].value, 0) == round(480 * 4.184, 0)


def test_salt_falls_back_to_sodium():
    fields = parse_nutrition_text("Salt 1.25 g")
    assert "sodium_mg" in fields
    assert round(fields["sodium_mg"].value, 0) == 500


def test_confidence_present():
    fields = parse_nutrition_text(LABEL)
    assert all(0 <= f.confidence <= 1 for f in fields.values())
