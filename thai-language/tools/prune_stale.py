#!/usr/bin/env python3
"""Drop translation rows whose English no longer exists in the installed game.

After a game patch, tools/extract.py rebuilds work/catalog.jsonl and tools/build_text.py refuses to
build while any row's (tag, en_sha) is missing from it ("STALE"). Those rows are either strings the
game removed or strings whose English changed; a changed one is re-translated as a NEW row (new
en_sha), so the old row can only ever be dead weight. Game patch 26334429 (2026-11-11): 178 rows.

  tools/prune_stale.py [--dry-run]

Refuses to run on an implausibly small catalogue, so a broken extract cannot wipe the translations.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
MIN_UNITS = 40000  # the catalogue held 46,781 units on 2026-11-11


def main(dry):
    path = os.path.join(MOD, 'work', 'catalog.jsonl')
    if not os.path.isfile(path):
        print('COULD NOT LOOK: work/catalog.jsonl missing — run tools/extract.py')
        return 2
    live = set()
    for line in open(path, encoding='utf-8'):
        u = json.loads(line)
        live.add((u['tag'], u['en_sha']))
    if len(live) < MIN_UNITS:
        print(f'COULD NOT LOOK: catalogue has only {len(live)} units (expected >= {MIN_UNITS}); not pruning')
        return 2
    total = kept = 0
    for p in sorted(glob.glob(os.path.join(MOD, 'translations', '*.jsonl'))):
        rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
        keep = [e for e in rows if (e['tag'], e['en_sha']) in live]
        gone = len(rows) - len(keep)
        total += gone
        kept += len(keep)
        if gone:
            print(f'{os.path.relpath(p, MOD)}: {gone} stale row(s)')
            if not dry:
                with open(p, 'w', encoding='utf-8') as f:
                    for e in keep:
                        f.write(json.dumps(e, ensure_ascii=False) + '\n')
    print(f'{total} stale row(s) {"would be removed" if dry else "removed"}; {kept} kept; catalogue {len(live)} units')
    return 0


if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
