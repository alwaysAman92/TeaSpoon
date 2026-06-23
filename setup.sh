#!/usr/bin/env bash
# TeaSpoon one-shot setup. Installs the backend + mobile app dependencies.
# Requires: Python 3.9+ and Node 18+ (with npm).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🥄  Setting up TeaSpoon in $ROOT"

echo "==> Backend (Python)"
cd "$ROOT/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
python -m app.seed
deactivate
echo "    backend ready."

echo "==> Mobile app (Expo)"
cd "$ROOT/mobile"
npm install
echo "    mobile ready."

cat <<'DONE'

✅  Setup complete. Now run, in three terminals:

  1) Backend API
     cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

  2) Mobile app (scan the QR with the Expo Go app on your phone)
     cd mobile && npx expo start

  3) Landing page (optional)
     cd website && python3 -m http.server 5173

To run the app on a physical phone, point it at your computer's LAN IP:
  cd mobile && EXPO_PUBLIC_API_BASE_URL=http://<your-ip>:8000 npx expo start
DONE
