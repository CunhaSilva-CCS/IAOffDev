#!/usr/bin/env bash
# Atalho: inicia o IAOffDev em modo aplicativo (janela), sem instalar no /Applications.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -d "$ROOT/frontend/dist" ]]; then
  (cd "$ROOT/frontend" && npm install && npm run build)
fi

cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt -r requirements-desktop.txt

export IAOFFDEV_APP_ROOT="$ROOT"
export IAOFFDEV_STATIC_DIR="$ROOT/frontend/dist"
export IAOFFDEV_WORKSPACE_ROOT="${IAOFFDEV_WORKSPACE_ROOT:-$HOME/Documents/IAOffDev}"
mkdir -p "$IAOFFDEV_WORKSPACE_ROOT"

exec python "$ROOT/desktop/launcher.py"
