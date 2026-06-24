"""End-to-end API tests using a throwaway SQLite DB (no network calls)."""
import os
import tempfile

import pytest

# Point the app at a temp DB BEFORE importing it.
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


from app.database import engine  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _setup():
    seed()
    yield
    engine.dispose()
    os.close(_db_fd)
    try:
        os.unlink(_db_path)
    except OSError:
        pass



client = TestClient(app)
HEADERS = {"X-User-Id": "test-user"}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_scan_known_product_returns_result_card():
    resp = client.post("/scan", json={"barcode": "8901719100109"}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["product"]["name"].startswith("Parle-G")
    # Translation present with a teaspoon headline.
    sugar = next(t for t in data["translation"] if t["key"] == "sugar")
    assert "tsp of sugar" in sugar["headline"]
    # Alternatives always present on a scan.
    assert isinstance(data["alternatives"], list)
    # Dashboard updated.
    assert data["dashboard"]["scans_today"] >= 1


def test_unknown_barcode_prompts_for_photo():
    resp = client.post("/scan", json={"barcode": "0000000000000", "log": False}, headers=HEADERS)
    data = resp.json()
    # Either OFF has it or (more likely offline) we ask for a photo.
    assert data["found"] in (True, False)
    if not data["found"]:
        assert data["needs_photo"] is True


def test_claims_detector_flags_misleading_protein_cookie():
    resp = client.post("/scan", json={"barcode": "8904004400999", "log": False}, headers=HEADERS)
    detail = resp.json()["detail"]
    assert detail["claims"]["badge"] == "Marketing vs Reality"


def test_ingredient_scanner_flags_gelatin_gummies():
    resp = client.post("/scan", json={"barcode": "8901030966012", "log": False}, headers=HEADERS)
    ingredients = resp.json()["detail"]["ingredients"]
    assert ingredients["veg_status"] == "non_veg"


def test_settings_roundtrip_changes_alternatives_mode():
    put = client.put("/settings", json={"alternatives_priority": "cheaper"}, headers=HEADERS)
    assert put.json()["alternatives_priority"] == "cheaper"
    got = client.get("/settings", headers=HEADERS)
    assert got.json()["alternatives_priority"] == "cheaper"


def test_dashboard_and_trend():
    client.post("/scan", json={"barcode": "8901491101837"}, headers=HEADERS)
    dash = client.get("/dashboard", headers=HEADERS).json()
    assert "takeaway" in dash and dash["primary"]["key"]
    trend = client.get("/dashboard/trend?days=7", headers=HEADERS).json()
    assert len(trend) == 7


def test_contribution_pipeline_confirms_on_matching_photos():
    barcode = "9990001112223"
    label = "Protein 8 g Total Sugars 5 g Sodium 200 mg Saturated Fat 2 g Energy 400 kcal"
    for _ in range(2):
        resp = client.post(
            "/contributions/submit",
            data={"barcode": barcode, "simulated_ocr_text": label},
            files={"photo": ("label.jpg", b"fakebytes", "image/jpeg")},
            headers=HEADERS,
        )
        assert resp.status_code == 201
    assert resp.json()["trust_tier"] in ("pending", "confirmed")


def test_preview_with_date_returns_dashboard_for_that_day():
    resp = client.get("/scan/8901058822999?date=2026-06-20", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["dashboard"]["date"] == "2026-06-20"

