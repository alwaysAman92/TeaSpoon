from app.core.alternatives import AltCandidate, rank_alternatives


def _c(id, name, sugar, sodium, fat, protein, stars, price):
    return AltCandidate(
        id=id, name=name, brand="b", category="biscuits",
        sugar_g=sugar, sodium_mg=sodium, saturated_fat_g=fat,
        protein_g=protein, hsr_stars=stars, price_inr=price,
    )


SCANNED = _c(1, "Sugary Biscuit", sugar=30, sodium=400, fat=10, protein=6, stars=1.5, price=40)

POOL = [
    _c(2, "Oat Biscuit", sugar=12, sodium=200, fat=3, protein=9, stars=3.5, price=60),
    _c(3, "Digestive", sugar=20, sodium=300, fat=6, protein=7, stars=2.5, price=35),
    _c(4, "Cream Biscuit", sugar=35, sodium=450, fat=12, protein=5, stars=1.0, price=25),
    AltCandidate(id=5, name="Other cat", brand="b", category="chips",
                 sugar_g=1, sodium_mg=10, saturated_fat_g=1, protein_g=1,
                 hsr_stars=4.0, price_inr=10),
]


def test_healthier_ranks_better_options_only():
    results = rank_alternatives(SCANNED, POOL, mode="healthier")
    assert len(results) >= 1
    ids = [r.candidate.id for r in results]
    assert 5 not in ids  # different category excluded
    assert 4 not in ids  # worse than scanned excluded
    assert results[0].candidate.id == 2  # healthiest first
    assert results[0].reason


def test_cheaper_requires_comparable_quality():
    # Cheaper mode: only products within ~10% HSR band AND cheaper.
    results = rank_alternatives(SCANNED, POOL, mode="cheaper")
    for r in results:
        assert r.candidate.price_inr < SCANNED.price_inr
        assert abs(r.candidate.hsr_stars - SCANNED.hsr_stars) <= max(0.5, SCANNED.hsr_stars * 0.10)


def test_limit_respected():
    results = rank_alternatives(SCANNED, POOL, mode="healthier", limit=1)
    assert len(results) <= 1
