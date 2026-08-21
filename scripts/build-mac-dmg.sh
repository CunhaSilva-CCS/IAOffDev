#!/usr/bin/env bash
# Gera IAOffDev.app + DMG para distribuição (rode no Mac).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/install-mac.sh" --user

STAGE_APP="$ROOT/dist/mac/IAOffDev.app"
# install-mac --user coloca em ~/Applications; espelha também em dist
if [[ -d "$HOME/Applications/IAOffDev.app" ]]; then
  rm -rf "$STAGE_APP"
  mkdir -p "$ROOT/dist/mac"
  cp -R "$HOME/Applications/IAOffDev.app" "$STAGE_APP"
fi

DMG="$ROOT/dist/mac/IAOffDev-1.0.0.dmg"
rm -f "$DMG"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "DMG só pode ser criado no macOS. Bundle em: $ROOT/dist/mac/"
  exit 0
fi

echo "==> Criando DMG"
TMP_DMG="$ROOT/dist/mac/dmg-root"
rm -rf "$TMP_DMG"
mkdir -p "$TMP_DMG"
cp -R "$STAGE_APP" "$TMP_DMG/IAOffDev.app"
ln -s /Applications "$TMP_DMG/Applications"

hdiutil create -volname "IAOffDev" -srcfolder "$TMP_DMG" -ov -format UDZO "$DMG"
rm -rf "$TMP_DMG"
echo "DMG: $DMG"
