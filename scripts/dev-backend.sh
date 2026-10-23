#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
# shellcheck disable=SC1091
source .venv/bin/activate
mkdir -p "$ROOT/data"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$ROOT/data/returnright.db}"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
