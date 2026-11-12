#!/bin/bash
# Copy the mod into Civ VII's local Mods folder (macOS). The gate runs first: a mod that fails
# tools/build.py is never installed. LTH_DEST overrides the target (tools/package.sh stages there).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${LTH_DEST:-$HOME/Library/Application Support/Civilization VII/Mods/lth-ayutthaya}"
# Needs pythainlp for the Thai word breaks: pip install -r ../thai-language/tools/requirements.txt,
# then point LTH_PYTHON at that interpreter.
"${LTH_PYTHON:-python3}" "$HERE/tools/build.py"
# A syntax error stops a UIScript from loading at all, silently.
for f in "$HERE"/ui/*.js; do node --check "$f" || { echo "SYNTAX ERROR: $f"; exit 1; }; done
mkdir -p "$DEST"
# ALLOWLIST: only what the game loads (the Thai pack learned this the hard way, 2026-11-06).
rsync -a --delete --delete-excluded \
  --include '/ayutthaya.modinfo' --include '/README.md' \
  --include '/config/' --include '/config/*.xml' \
  --include '/data/' --include '/data/*.xml' --include '/data/icons/' --include '/data/icons/*.xml' \
  --include '/art/' --include '/art/bg-panel-lth_ayutthaya' --include '/art/bg-panel-lth_ayutthaya.png' --include '/art/lth_ayutthaya_vert.png' --include '/ui/' --include '/ui/*.js' \
  --include '/text/' --include '/text/gen/' --include '/text/gen/*.xml' \
  --exclude '*' "$HERE/" "$DEST/"
echo "installed -> $DEST"
