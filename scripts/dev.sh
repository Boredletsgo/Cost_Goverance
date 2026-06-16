#!/usr/bin/env bash
#
# One-command local bootstrap for InfraMind (no Docker required).
#
# Creates the backend virtualenv, installs the lite dependency set, initializes
# and seeds a local SQLite database, then starts the FastAPI backend and the Vite
# frontend. Uses the built-in mock LLM and hashing embedder, so NO API keys and
# NO Postgres/Redis are required.
#
# Usage:
#   ./scripts/dev.sh            # start (seeds only on first run)
#   ./scripts/dev.sh --reseed   # force re-init + re-seed of the database
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESEED=0
[[ "${1:-}" == "--reseed" ]] && RESEED=1

echo "==> InfraMind local bootstrap (SQLite + mock LLM, no Docker)"

# --- Backend ---------------------------------------------------------------
cd "$REPO/backend"

if [[ ! -d .venv ]]; then
  echo "==> Creating Python virtual environment..."
  python3 -m venv .venv
fi

PY="$REPO/backend/.venv/bin/python"

echo "==> Installing backend dependencies (lite)..."
"$PY" -m pip install --upgrade pip --quiet
"$PY" -m pip install -r requirements.txt --quiet

if [[ "$RESEED" == "1" || ! -f .data/inframind.db ]]; then
  echo "==> Initializing and seeding database..."
  "$PY" -m app.cli init-db
  "$PY" -m app.cli seed
else
  echo "==> Database already present; skipping seed (use --reseed to force)."
fi

echo "==> Starting backend at http://127.0.0.1:8000 (docs: /docs) ..."
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
trap 'echo; echo "==> Stopping backend (pid $BACKEND_PID)"; kill "$BACKEND_PID" 2>/dev/null || true' EXIT

# --- Frontend --------------------------------------------------------------
cd "$REPO/frontend"

if [[ ! -d node_modules ]]; then
  echo "==> Installing frontend dependencies..."
  npm install
fi

echo "==> Starting frontend at http://localhost:5173 ..."
echo "    (Press Ctrl+C to stop both frontend and backend.)"
npm run dev
