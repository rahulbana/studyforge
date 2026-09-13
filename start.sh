#!/usr/bin/env bash
# Starts the FastAPI backend (port 8000) and the Vite frontend (port 5173).
# Ctrl-C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ ! -d backend/.venv ]; then
  echo "ERROR: backend/.venv not found. Run ./setup.sh first." >&2
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "ERROR: frontend/node_modules not found. Run ./setup.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source backend/.venv/bin/activate

# --- Database preflight ---------------------------------------------------
# Verify the DB is reachable and the schema is current (auto-creates/upgrades),
# and abort with a clear message if not — before starting the app.
echo "==> Checking database…"
if ! ( cd backend && python -m app.db.doctor ); then
  echo "ERROR: database preflight failed (see above)." >&2
  echo "       Fix DATABASE_URL in backend/.env or start your database, then retry." >&2
  exit 1
fi

echo "==> Starting backend on http://localhost:8000"
( cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload ) &
BACKEND_PID=$!

echo "==> Starting frontend on http://localhost:5173"
( cd frontend && npm run dev ) &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "==> Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo ""
echo "============================================================"
echo " App running:"
echo "   Frontend  ->  http://localhost:5173"
echo "   API docs  ->  http://localhost:8000/docs"
echo " Press Ctrl-C to stop."
echo "============================================================"

wait
