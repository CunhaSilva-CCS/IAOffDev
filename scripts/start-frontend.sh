#!/usr/bin/env bash
# Inicia o frontend IAOffDev
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if [[ ! -d node_modules ]]; then
  npm install
fi

echo "IAOffDev UI em http://127.0.0.1:5173"
exec npm run dev
