#!/usr/bin/env python3
"""Remove the space translators put between Thai words and a [TIP] link.

Thai does not separate words with spaces, but the brief asked for "a space around icons", and batches
read [TIP:...]word[/TIP] as one. The result shows in game as a visible gap inside a phrase:
"ยูนิตทางบก ที่ฝึกในถิ่นฐาน นี้" (LOC_BUILDING_BARRACKS tooltip, screenshot 2026-11-06 15:14).
Measured that day: 2,884 such spaces in 1,636 rows.

Only a space with Thai on BOTH sides of the link boundary is removed:
    <Thai> [TIP:...]<Thai>     ->  <Thai>[TIP:...]<Thai>
    <Thai>[/TIP] <Thai>        ->  <Thai>[/TIP]<Thai>
A space next to a number, an icon, Latin text or punctuation is kept.

  tools/fix_tip_spaces.py [--dry-run]       tools/check.py fails while any remain.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
T = '฀-๿'
BEFORE_TIP = re.compile(rf'(?<=[{T}]) (?=\[TIP:[^\]]*\][{T}])')
AFTER_TIP = re.compile(rf'(?<=[{T}]\[/TIP\]) (?=[{T}])')


def fix(th):
    return AFTER_TIP.sub('', BEFORE_TIP.sub('', th))


def count(th):
    return len(BEFORE_TIP.findall(th)) + len(AFTER_TIP.findall(th))


def main(dry):
    total = rows = 0
    for p in sorted(glob.glob(os.path.join(MOD, 'translations', '*.jsonl'))):
        data = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
        changed = 0
        for e in data:
            n = count(e['th'])
            if n:
                total += n
                changed += 1
                e['th'] = fix(e['th'])
        rows += changed
        if changed and not dry:
            with open(p, 'w', encoding='utf-8') as f:
                for e in data:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
    print(f'{total} space(s) in {rows} row(s) {"would be removed" if dry else "removed"}')
    return 0


if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
