#!/usr/bin/env bash
# Sobe backend + frontend (dois processos)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

"$ROOT/scripts/start-backend.sh" &
BACK_PID=$!
"$ROOT/scripts/start-frontend.sh" &
FRONT_PID=$!

cleanup() {
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
