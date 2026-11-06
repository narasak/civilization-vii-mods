#!/bin/bash
# Build a release zip and a Steam Workshop content folder from the SAME build + gate as install.sh.
#   tools/package.sh            -> dist/lth-thai-language/ (Workshop content) and dist/thai-language-pack-v<N>.zip
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VER=$(sed -n 's/.*<Mod id="lth-thai-language" version="\([0-9]*\)".*/\1/p' "$HERE/thai-language.modinfo")
[ -n "$VER" ] || { echo "COULD NOT LOOK: no integer version in thai-language.modinfo"; exit 2; }
STAGE="$HERE/dist/lth-thai-language"
rm -rf "$STAGE"
LTH_DEST="$STAGE" "$HERE/tools/install.sh"
ZIP="$HERE/dist/thai-language-pack-v$VER.zip"
rm -f "$ZIP"
(cd "$HERE/dist" && zip -qr "$ZIP" lth-thai-language -x '*.DS_Store')
n=$(unzip -l "$ZIP" | tail -1 | awk '{print $2}')
[ "$n" -ge 15 ] || { echo "PACKAGE IMPLAUSIBLE: only $n files in $ZIP"; exit 1; }
echo "packaged $n files -> $ZIP ($(du -h "$ZIP" | cut -f1))"
