from app.core import ledger


def test_totals_accumulate():
    totals = ledger.DailyTotals()
    totals.add(ledger.ScanEntry(sugar_g=20, sodium_mg=600, protein_g=10))
    totals.add(ledger.ScanEntry(sugar_g=4, sodium_mg=600, protein_g=8))
    assert totals.sugar_g == 24
    assert totals.sodium_mg == 1200
    assert totals.protein_g == 18


def test_negative_contributions_clamped():
    totals = ledger.DailyTotals()
    totals.add(ledger.ScanEntry(sugar_g=-10, sodium_mg=-5))
    assert totals.sugar_g == 0
    assert totals.sodium_mg == 0


def test_dashboard_reproduces_prd_example():
    # PRD: "6 of 10 tsp sugar", "60% of sodium limit", "38g of 70g protein goal"
    totals = ledger.DailyTotals(sugar_g=24, sodium_mg=1200, protein_g=38)
    dash = ledger.build_dashboard(totals, primary_key="sugar")
    assert dash.primary.headline == "6 of 10 tsp sugar"
    sodium = next(s for s in dash.secondary if s.key == "sodium")
    protein = next(s for s in dash.secondary if s.key == "protein")
    assert sodium.headline == "60% of sodium limit"
    assert protein.headline == "38g of 70g protein goal"


def test_takeaway_thresholds():
    over = ledger.build_dashboard(ledger.DailyTotals(sugar_g=48), primary_key="sugar")
    assert "Over budget" in over.takeaway

    near = ledger.build_dashboard(ledger.DailyTotals(sugar_g=36), primary_key="sugar")
    assert "90%" in near.takeaway or "Careful" in near.takeaway

    empty = ledger.build_dashboard(ledger.DailyTotals(), primary_key="sugar")
    assert "clean slate" in empty.takeaway.lower()


def test_health_profile_tightens_limits():
    targets = ledger.resolve_targets_for_profile(["diabetic", "hypertensive"])
    assert targets["sugar_tsp"] == 6.0
    assert targets["sodium_mg"] == 1500.0
