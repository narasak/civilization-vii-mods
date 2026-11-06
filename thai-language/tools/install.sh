#!/bin/bash
# Copy the mod into Civ VII's local Mods folder (macOS). Runs the gate first: a mod that fails
# the check is never installed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/Library/Application Support/Civilization VII/Mods/lth-thai-language"

# Generated text first (needs fonttools + pythainlp: pip install -r tools/requirements.txt;
# point LTH_PYTHON at that interpreter), then the gate reads what was generated.
"${LTH_PYTHON:-python3}" "$HERE/tools/build_text.py"
"${LTH_PYTHON:-python3}" "$HERE/tools/build_css.py"
"${LTH_PYTHON:-python3}" "$HERE/tools/check.py"
# A syntax error stops a UIScript from loading at all, silently. node --check caught a comment that
# closed itself early ("BodyFont*/") on 2026-11-06.
for f in "$HERE"/ui/*.js; do node --check "$f" || { echo "SYNTAX ERROR: $f"; exit 1; }; done
for f in lth-Sarabun-Regular lth-Sarabun-SemiBold lth-Kanit-Medium lth-Kanit-SemiBold; do
  [ -f "$HERE/fonts/$f.ttf" ] || { echo "MISSING fonts/$f.ttf — run tools/build-fonts.py"; exit 1; }
done

mkdir -p "$DEST"
rsync -a --delete --delete-excluded --exclude tools --exclude work --exclude translations --exclude glossary --exclude .gitignore --exclude fonts/src --exclude '.DS_Store' "$HERE/" "$DEST/"
echo "installed -> $DEST"
