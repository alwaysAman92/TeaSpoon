# TeaSpoon Backend

Python · FastAPI · SQLAlchemy. Houses the deterministic core logic (translation,
ledger, HSR, NOVA, claims, ingredients) and the API that the app talks to.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

## Layout

```
app/
  core/            # pure, deterministic, unit-tested logic (PRD Phase 0)
    translation.py # F2 grams -> teaspoons / % daily limit
    ledger.py      # F3/F4 daily totals + dashboard takeaway
    hsr.py         # F6 Health Star Rating (FSANZ structure)
    nova.py        # F7 processing classification
    claims.py      # F8 marketing-vs-reality detector
    ingredients.py # F9 INS codes + veg/non-veg flags
    alternatives.py# F5 healthier / cheaper ranking
  services/        # orchestration: OFF client, OCR, scan, ledger, contributions
  routers/         # FastAPI routes
  models.py        # SQLAlchemy ORM (catalogue, ledger, trust tiers, versions)
  data/seed_products.json  # 24 real Indian SKUs
tests/             # 46 tests
```

## Key endpoints

| Method & path            | Purpose                                  |
| ------------------------ | ---------------------------------------- |
| `POST /scan`             | Scan a barcode → result card + log it    |
| `GET  /scan/{barcode}`   | Preview without logging (manual entry)   |
| `GET  /dashboard`        | Today's totals + bold takeaway           |
| `GET  /dashboard/trend`  | 7-day trend                              |
| `GET/PUT /settings`      | Alternatives priority, primary nutrient, health profile |
| `POST /contributions/submit` | Submit a label photo (Section 10)    |
| `POST /products/report`  | "Report incorrect data"                  |

## Config

Copy `.env.example` → `.env`. Secrets (DB URL, Clerk, Google Vision) come from the
environment only — never hard-coded. SQLite is the default dev database.

## Tests

```bash
pytest
```
