# TeaSpoon 🥄

**Know it in teaspoons, not grams.**

TeaSpoon is a daily nutrition-tracking app for India. Scan the barcode of any
packaged food or drink and instantly see its sugar, sodium and protein in plain
language — teaspoons and % of your daily limit, not confusing gram counts. Every
scan adds to a running daily total and surfaces 1–3 better alternatives.

This repository implements the [TeaSpoon PRD v5.0](#) end to end.

```
Scan → see it in teaspoons → see an alternative either way → watch today's total update → come back tomorrow.
```

## What's in the box

| Folder       | What it is                          | Stack                                   |
| ------------ | ----------------------------------- | --------------------------------------- |
| `backend/`   | API + the deterministic core logic  | Python · FastAPI · SQLAlchemy · SQLite/Postgres |
| `mobile/`    | The app (Scan / Result / Dashboard / Settings) | React Native · Expo · TypeScript        |
| `website/`   | The landing page (Section 8)        | Static HTML / CSS / JS                  |

## Feature → code map

| PRD feature | Where it lives |
| --- | --- |
| F1 Barcode scanner | `mobile/src/screens/ScanScreen.tsx` (expo-camera) |
| F2 Plain-language translation | `backend/app/core/translation.py` |
| F3 Daily ledger | `backend/app/core/ledger.py` + `services/ledger_service.py` |
| F4 Daily dashboard | `mobile/src/screens/DashboardScreen.tsx` |
| F5 Alternatives on every scan | `backend/app/core/alternatives.py` |
| F6 Health Star Rating | `backend/app/core/hsr.py` |
| F7 NOVA classification | `backend/app/core/nova.py` |
| F8 Misleading claims detector | `backend/app/core/claims.py` |
| F9 Ingredient & veg/non-veg scanner | `backend/app/core/ingredients.py` |
| §10 Photo submission, trust tiers, OCR | `backend/app/services/{ocr,contribution}_service.py` |

## Quick start

### 1. Backend (the brain)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed                       # load 24 real Indian SKUs into SQLite
uvicorn app.main:app --reload            # http://localhost:8000/docs
```

Run the tests (the core maths is fully unit-tested — PRD Phase 0):

```bash
pytest          # 46 tests
```

### 2. Mobile app

```bash
cd mobile
npm install
npx expo start                           # press i / a, or scan the QR in Expo Go
```

> The app reads `extra.apiBaseUrl` from `app.json` (defaults to
> `http://localhost:8000`). On a physical device, set it to your machine's LAN IP,
> or export `EXPO_PUBLIC_API_BASE_URL=http://<your-ip>:8000`.

### 3. Landing page

```bash
cd website
python3 -m http.server 5173              # http://localhost:5173
```

## Design language

Bold one-line statements, oversized hero numbers, swipeable cards, minimal
chrome, generous whitespace (PRD Section 7). Both the app and the landing page
share the same palette — ink `#14110E`, cream `#FBF7F0`, sugar-amber `#FF5A1F`.

## Notes & honest caveats

- **HSR tables** (`backend/app/core/hsr.py`) implement the FSANZ calculation
  *structure* faithfully — categories, baseline vs modifying points, the
  protein-gating rule, and 0.5–5★ mapping. The numeric cut-offs are isolated in
  one `HSR_TABLES` dict; validate them line-by-line against the official FSANZ
  Calculator v9 before relying on the star output in production.
- **Auth** uses an `X-User-Id` header for the MVP; swap in Clerk JWT verification
  (PRD Section 11) for production.
- **OCR** calls Google Cloud Vision when `GOOGLE_CLOUD_VISION_API_KEY` is set; the
  text→nutrient parser is pure and unit-tested so the pipeline works without it.
- **Dev DB** is SQLite for zero-setup; point `DATABASE_URL` at PostgreSQL for prod
  (`pip install -r requirements-prod.txt`).
```
