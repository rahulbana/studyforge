#!/usr/bin/env bash
# Fresh setup: removes any existing environment (venv, node_modules) and the
# .env file, then recreates the Python venv (python3.12), installs backend and
# frontend dependencies, and prepares a new .env file.
#
# A real OPENAI_API_KEY already in backend/.env is preserved across the wipe and
# restored into the new .env (the "sk-..." placeholder is not preserved).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> StudyForge — setup"

# --- Preserve a real API key before wiping .env ---------------------------
# Capture an existing, non-placeholder OPENAI_API_KEY so a clean reinstall
# doesn't force you to paste your key again every time.
PRESERVED_KEY=""
if [ -f backend/.env ]; then
  existing_key="$(sed -n 's/^OPENAI_API_KEY=//p' backend/.env | head -n1)"
  existing_key="${existing_key%\"}"; existing_key="${existing_key#\"}"
  existing_key="${existing_key%\'}"; existing_key="${existing_key#\'}"
  existing_key="$(printf '%s' "$existing_key" | tr -d '[:space:]')"
  # Keep it only if it looks like a real key: starts with sk-, no "..."
  # placeholder, and at least 20 chars long.
  if [ -n "$existing_key" ] \
     && [ "${existing_key#sk-}" != "$existing_key" ] \
     && [ "${existing_key%...*}" = "$existing_key" ] \
     && [ "${#existing_key}" -ge 20 ]; then
    PRESERVED_KEY="$existing_key"
  fi
fi

# --- Clean slate: remove any existing environment -------------------------
# Wipes the previous install so setup always starts from scratch. A real
# OPENAI_API_KEY (captured above) is restored into the new .env afterwards.
echo "==> Removing any existing environment (venv, node_modules, .env)"
if [ -d backend/.venv ]; then
  echo "    - removing backend/.venv"
  rm -rf backend/.venv
fi
if [ -f backend/.env ]; then
  if [ -n "$PRESERVED_KEY" ]; then
    echo "    - removing backend/.env (preserving your OPENAI_API_KEY)"
  else
    echo "    - removing backend/.env"
  fi
  rm -f backend/.env
fi
if [ -d frontend/node_modules ]; then
  echo "    - removing frontend/node_modules"
  rm -rf frontend/node_modules
fi

# --- Python version check -------------------------------------------------
PY=python3.12
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "ERROR: python3.12 not found on PATH. Please install Python 3.12." >&2
  exit 1
fi
echo "==> Using $($PY --version)"

# --- Backend virtual environment -----------------------------------------
echo "==> Creating virtual environment at backend/.venv"
"$PY" -m venv backend/.venv
# shellcheck disable=SC1091
source backend/.venv/bin/activate

echo "==> Upgrading pip"
python -m pip install --upgrade pip >/dev/null

echo "==> Installing backend dependencies (with dev tools: pytest, ruff)"
pip install -r backend/requirements-dev.txt

# --- .env -----------------------------------------------------------------
cp backend/.env.example backend/.env
if [ -n "$PRESERVED_KEY" ]; then
  # Restore the preserved key. awk -v avoids sed escaping issues with the value.
  awk -v k="$PRESERVED_KEY" \
    '/^OPENAI_API_KEY=/{print "OPENAI_API_KEY=" k; next} {print}' \
    backend/.env > backend/.env.tmp && mv backend/.env.tmp backend/.env
  echo "==> Created backend/.env and restored your existing OPENAI_API_KEY"
else
  echo "==> Created a fresh backend/.env  (edit it and add your OPENAI_API_KEY)"
fi

deactivate

# --- Frontend -------------------------------------------------------------
if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm not found on PATH. Please install Node.js 18+." >&2
  exit 1
fi
echo "==> Installing frontend dependencies (npm install)"
cd frontend
npm install
cd "$ROOT"

echo ""
echo "============================================================"
echo " Setup complete."
if [ -n "$PRESERVED_KEY" ]; then
  echo " 1. Your OPENAI_API_KEY was preserved in backend/.env"
else
  echo " 1. Add your OpenAI API key to backend/.env"
fi
echo " 2. Run ./start.sh to launch the app"
echo "============================================================"
