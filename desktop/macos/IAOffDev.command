#!/bin/bash
# Executável do bundle IAOffDev.app (macOS)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCES="$ROOT/Resources"
export IAOFFDEV_APP_ROOT="$RESOURCES"
export IAOFFDEV_STATIC_DIR="$RESOURCES/ui"
export IAOFFDEV_WORKSPACE_ROOT="${IAOFFDEV_WORKSPACE_ROOT:-$HOME/Documents/IAOffDev}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$RESOURCES/venv/bin:$PATH"

mkdir -p "$IAOFFDEV_WORKSPACE_ROOT"

VENV="$RESOURCES/venv"
LOG="$HOME/Library/Logs/IAOffDev.log"
mkdir -p "$(dirname "$LOG")"

pick_python() {
  if [[ -x "$VENV/bin/python" ]]; then
    echo "$VENV/bin/python"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  return 1
}

if ! PYTHON_BIN="$(pick_python)"; then
  osascript -e 'display dialog "Python 3 não encontrado.\n\nInstale com:\n  brew install python\nou pelo site python.org\n\nDepois abra o IAOffDev novamente." buttons {"OK"} default button 1 with title "IAOffDev" with icon caution'
  exit 1
fi

if [[ ! -x "$VENV/bin/python" ]] || [[ ! -f "$VENV/.iaoffdev-ready" ]]; then
  osascript <<'APPLESCRIPT' >/dev/null 2>&1 &
display notification "Preparando o ambiente na primeira abertura…" with title "IAOffDev"
APPLESCRIPT
  {
    echo "=== $(date) setup venv ==="
    "$PYTHON_BIN" -m venv "$VENV"
    "$VENV/bin/python" -m pip install --upgrade pip
    "$VENV/bin/python" -m pip install \
      -r "$RESOURCES/backend/requirements.txt" \
      -r "$RESOURCES/backend/requirements-desktop.txt"
    touch "$VENV/.iaoffdev-ready"
    echo "=== setup ok ==="
  } >>"$LOG" 2>&1 || {
    osascript -e "display dialog \"Falha ao preparar o IAOffDev. Veja o log:\\n$LOG\" buttons {\"OK\"} default button 1 with title \"IAOffDev\" with icon stop"
    exit 1
  }
fi

cd "$RESOURCES"
exec "$VENV/bin/python" "$RESOURCES/launcher.py" >>"$LOG" 2>&1
