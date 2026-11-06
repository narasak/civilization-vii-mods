#!/usr/bin/env python3
"""One Thai per English NAME, across every translation file.

Parallel batches name the same thing differently (2026-11-06: 30 conflicts after the first merge of
the Exploration/Modern/DLC names). For every *_NAME row whose English has more than one Thai, this
rewrites them all to one canonical form: TIES below when decided by hand, otherwise the variant used
most often. Homonyms (glossary/homonyms.tsv) are left alone. Then re-run `tools/batch.py names`.

  tools/unify_names.py [--dry-run]
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)

# Hand decisions where counts tie or the majority is wrong.
TIES = {
    'Corsair': 'เรือคอร์แซร์',                        # unit; Privateer is เรือโจรสลัดรับอนุญาต
    'Demand Tribute': 'เรียกร้องบรรณาการ',
    'Evangelism': 'การเผยแผ่ศาสนา',
    'House of Wisdom': 'สภาแห่งปัญญา',
    'Ideological Revolt': 'การกบฏทางอุดมการณ์',
    'Ranged Army': 'กองทัพระยะไกล',
    'Rashidun': 'รอชิดีน',
    'Revolutionary Authoritarianism': 'อำนาจนิยมแบบปฏิวัติ',
    'Revolutionary Republic': 'สาธารณรัฐปฏิวัติ',
    'Saqiya': 'ซากียะฮ์',
    'Stone Head': 'เศียรศิลา',
    'Consuetudines et Justicie': 'คอนซูเอตูดีเนส เอต ยุสติกิเอ',
    'Muzibu Azaala Mpanga': 'มูซีบู อาซาลา มปังกา',
    'Megalopolis': 'อภิมหานคร',                     # a meaning Thai readers get, over a transliteration
}


def main(dry):
    cat = {}
    for line in open(os.path.join(MOD, 'work', 'catalog.jsonl'), encoding='utf-8'):
        u = json.loads(line)
        cat[(u['tag'], u['en_sha'])] = u['en'].strip()
    hpath = os.path.join(MOD, 'glossary', 'homonyms.tsv')
    homonyms = {l.split('\t')[0] for l in open(hpath, encoding='utf-8').read().splitlines()[1:]} if os.path.isfile(hpath) else set()

    files = sorted(glob.glob(os.path.join(MOD, 'translations', '*.jsonl')))
    data = {p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()] for p in files}
    variants = defaultdict(Counter)
    for rows in data.values():
        for e in rows:
            en = cat.get((e['tag'], e['en_sha']))
            if en and e['tag'].endswith('_NAME') and en not in homonyms:
                variants[en][e['th']] += 1
    canon = {}
    for en, c in variants.items():
        if len(c) > 1:
            canon[en] = TIES.get(en) or c.most_common(1)[0][0]
    changed = 0
    for p, rows in data.items():
        n = 0
        for e in rows:
            en = cat.get((e['tag'], e['en_sha']))
            if en in canon and e['tag'].endswith('_NAME') and e['th'] != canon[en]:
                e['th'] = canon[en]
                n += 1
        if n and not dry:
            with open(p, 'w', encoding='utf-8') as f:
                for e in rows:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
        changed += n
    for en in sorted(canon):
        print(f'{en} -> {canon[en]}')
    print(f'{len(canon)} conflicting name(s); {changed} row(s) {"would change" if dry else "changed"}')
    return 0


if __name__ == '__main__':
    sys.exit(main('--dry-run' in sys.argv))
