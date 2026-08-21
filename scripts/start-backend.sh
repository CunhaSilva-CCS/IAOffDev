#!/usr/bin/env bash
# Inicia o backend IAOffDev
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

export IAOFFDEV_HOST="${IAOFFDEV_HOST:-127.0.0.1}"
export IAOFFDEV_PORT="${IAOFFDEV_PORT:-8765}"
export IAOFFDEV_WORKSPACE_ROOT="${IAOFFDEV_WORKSPACE_ROOT:-$HOME/projects}"

echo "IAOffDev API em http://${IAOFFDEV_HOST}:${IAOFFDEV_PORT}"
exec python run.py
