#!/usr/bin/env bash
# Instala o IAOffDev como aplicativo no Mac (Arraste/Apps / Applications).
# Uso (no Mac, na pasta do projeto):
#   ./scripts/install-mac.sh
#   ./scripts/install-mac.sh --user    # instala em ~/Applications
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-}"
DEST_BASE="/Applications"
if [[ "$MODE" == "--user" ]]; then
  DEST_BASE="$HOME/Applications"
  mkdir -p "$DEST_BASE"
fi

APP_NAME="IAOffDev.app"
APP_DIR="$DEST_BASE/$APP_NAME"
STAGE="$ROOT/dist/mac/$APP_NAME"

echo "==> IAOffDev — instalador para macOS"
echo "    Destino: $APP_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Aviso: este script é para macOS. Continuando só a montagem do bundle em dist/mac/."
fi

command -v python3 >/dev/null || { echo "Python 3 é obrigatório"; exit 1; }
command -v npm >/dev/null || { echo "Node.js/npm é obrigatório para gerar a interface"; exit 1; }

echo "==> Build da interface"
(
  cd "$ROOT/frontend"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run build
)

echo "==> Montando $APP_NAME"
rm -rf "$STAGE"
mkdir -p "$STAGE/Contents/MacOS" "$STAGE/Contents/Resources"

cp "$ROOT/desktop/macos/Info.plist" "$STAGE/Contents/Info.plist"
cp "$ROOT/desktop/macos/IAOffDev.command" "$STAGE/Contents/MacOS/IAOffDev"
chmod +x "$STAGE/Contents/MacOS/IAOffDev"

# Recursos do app
cp "$ROOT/desktop/launcher.py" "$STAGE/Contents/Resources/launcher.py"
cp -R "$ROOT/backend" "$STAGE/Contents/Resources/backend"
rm -rf "$STAGE/Contents/Resources/backend/.venv" \
       "$STAGE/Contents/Resources/backend/__pycache__" \
       "$STAGE/Contents/Resources/backend/app/__pycache__" \
       "$STAGE/Contents/Resources/backend/tests"
cp -R "$ROOT/frontend/dist" "$STAGE/Contents/Resources/ui"

# Ícone (PNG + icns se ferramentas existirem)
ICON_SRC="$ROOT/desktop/macos/AppIcon.svg"
ICON_RES="$STAGE/Contents/Resources"
if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 1024 -h 1024 "$ICON_SRC" -o "$ICON_RES/AppIcon.png"
elif command -v magick >/dev/null 2>&1; then
  magick -background none "$ICON_SRC" -resize 1024x1024 "$ICON_RES/AppIcon.png"
elif command -v convert >/dev/null 2>&1; then
  convert -background none "$ICON_SRC" -resize 1024x1024 "$ICON_RES/AppIcon.png"
else
  cp "$ICON_SRC" "$ICON_RES/AppIcon.svg"
fi

if [[ -f "$ICON_RES/AppIcon.png" ]] && [[ "$(uname -s)" == "Darwin" ]]; then
  ICONSET="$ICON_RES/AppIcon.iconset"
  mkdir -p "$ICONSET"
  for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" "$ICON_RES/AppIcon.png" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    sips -z $((size * 2)) $((size * 2)) "$ICON_RES/AppIcon.png" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o "$ICON_RES/AppIcon.icns"
  rm -rf "$ICONSET"
fi

# requirements desktop junto do backend
cp "$ROOT/backend/requirements-desktop.txt" "$STAGE/Contents/Resources/backend/requirements-desktop.txt"

# Pré-cria venv no bundle apenas no macOS (venv é específico da plataforma)
if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "==> Criando ambiente Python do app"
  python3 -m venv "$STAGE/Contents/Resources/venv"
  "$STAGE/Contents/Resources/venv/bin/pip" install --upgrade pip
  "$STAGE/Contents/Resources/venv/bin/pip" install \
    -r "$STAGE/Contents/Resources/backend/requirements.txt" \
    -r "$STAGE/Contents/Resources/backend/requirements-desktop.txt"
else
  echo "==> Pulando venv (não é macOS). Ele será criado na 1ª abertura no Mac."
fi

# PkgInfo
echo -n "APPL????" > "$STAGE/Contents/PkgInfo"

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "==> Instalando em $APP_DIR"
  rm -rf "$APP_DIR"
  mkdir -p "$DEST_BASE"
  cp -R "$STAGE" "$APP_DIR"
  # Remove quarentena de apps baixados/copiados
  xattr -dr com.apple.quarantine "$APP_DIR" 2>/dev/null || true
  echo
  echo "Pronto! Abra pelo Launchpad ou:"
  echo "  open \"$APP_DIR\""
  echo
  echo "Recomendado (IA local):"
  echo "  brew install ollama"
  echo "  ollama serve"
  echo "  ollama pull qwen2.5-coder:7b"
else
  echo
  echo "Bundle gerado em: $STAGE"
  echo "Copie esta pasta .app para um Mac e mova para /Applications."
fi
