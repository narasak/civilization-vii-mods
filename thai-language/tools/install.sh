#!/bin/bash
# Copy the mod into Civ VII's local Mods folder (macOS). Runs the gate first: a mod that fails
# the check is never installed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
# LTH_DEST overrides the target (tools/package.sh stages a release there).
DEST="${LTH_DEST:-$HOME/Library/Application Support/Civilization VII/Mods/lth-thai-language}"

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
# ALLOWLIST: only what the game loads plus the font licences. This was an exclude list until
# 2026-11-06, when new folders (dist/, workshop/) silently rode along into the v10 package.
rsync -a --delete --delete-excluded \
  --include '/thai-language.modinfo' --include '/README.md' \
  --include '/text/' --include '/text/gen/' --include '/text/gen/*.xml' \
  --include '/ui/' --include '/ui/*.js' \
  --include '/fonts/' --include '/fonts/lth-*.ttf' --include '/fonts/OFL-*.txt' \
  --include '/core/' --include '/core/ui/' --include '/core/ui/themes/' --include '/core/ui/themes/default/' \
  --include '/core/ui/themes/default/panel-animations.css' \
  --exclude '*' "$HERE/" "$DEST/"
echo "installed -> $DEST"
