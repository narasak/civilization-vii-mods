#!/bin/bash
# After a test run: was the mod ACTIVATED (not merely discovered), what did it measure, which font
# URLs failed, and did the game crash.
L="$HOME/Library/Application Support/Civilization VII/Logs"
[ -f "$L/UI.log" ] && [ -f "$L/Modding.log" ] || { echo "COULD NOT LOOK: logs missing in $L"; exit 2; }

echo "== activation (Modding.log 'Target Mods' blocks — discovery alone does not load a mod)"
awk '/Reason:/{reason=$0} /Target Mods/{inblk=1; hit=0; next}
     inblk && /lth-thai-language/{hit=1}
     inblk && /Game configuration|Performing/{ if (reason!="") print (hit?"  ACTIVE   ":"  INACTIVE ") substr(reason, index(reason,"Reason:")); inblk=0 }' "$L/Modding.log"

echo "== LTH measurements (UI.log)"
grep -n "LTH:" "$L/UI.log" || echo "  none — lth-thai-fonts.js never ran"
echo "== tight line-height on wrapped Thai (UI.log 'LTH: leading', every place found this run)"
grep -o 'LTH: leading .*' "$L/UI.log" | python3 -c '
import sys, json
spots, scans, worst = {}, 0, 0
for line in sys.stdin:
    try: d = json.loads(line.split("LTH: leading ", 1)[1])
    except Exception: continue
    scans += 1; worst = max(worst, d.get("ms", 0))
    for f in d.get("found", []): spots.setdefault(f["el"], f)
print(f"  {scans} scan(s), slowest {worst} ms, {len(spots)} place(s)")
for k, f in spots.items(): print(f"  {f[\"ratio\"]}  {k}  [{f[\"text\"]}]")
'
echo "== font URLs that failed (UI.log)"
grep -n "lth-.*\.ttf" "$L/UI.log" | head -20 || echo "  none failed"
grep -n "font fallback" "$L/UI.log" | head -5
echo "== text load issues (Database.log / Modding.log)"
grep -n -i "th-phase0\|lth-" "$L/Database.log" "$L/Modding.log" | grep -i -E "error|warn|fail" || echo "  none"
echo "== crash reports since this run started"
start=$(stat -f %m "$L/Modding.log" 2>/dev/null)
find "$HOME/Library/Logs/DiagnosticReports" -name 'CivilizationVII-*.ips' -newer "$L/Database.log" 2>/dev/null | sed 's/^/  CRASH /' || true
