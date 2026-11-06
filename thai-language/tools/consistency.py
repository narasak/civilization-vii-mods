#!/usr/bin/env python3
"""Report rows whose English mentions a canonical name/term but whose Thai does not use its Thai.

  tools/consistency.py [module ...]      (default: every translations/*.jsonl)

Sources of canonical Thai: glossary/names.tsv (translated *_NAME rows) and glossary/terms.tsv.
This is a REVIEW report, not a gate: a Thai sentence may legitimately rephrase or drop a word.
It prints per-term counts so a whole term going wrong (a batch ignoring names.tsv) stands out,
and exits 0. Names shorter than 4 letters, or English common words, are skipped to keep noise down.
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
MARKUP = re.compile(r'\{[^{}]*\}|\[[^\[\]]*\]')
COMMON = {'Age', 'Turn', 'Unit', 'City', 'Town', 'Gold', 'Food', 'Order', 'World', 'Active', 'Random',
          'Modern', 'Military', 'Cultural', 'Economic', 'Scientific'}  # too generic to flag by word


def read_tsv(path):
    if not os.path.isfile(path):
        return []
    lines = open(path, encoding='utf-8').read().splitlines()
    return [l.split('\t') for l in lines[1:] if l.strip()]


def main(mods):
    canon = {}
    for row in read_tsv(os.path.join(MOD, 'glossary', 'terms.tsv')):
        canon[row[0]] = row[1]
    # Only entity names: a setup option called "Quick" or "Service" is not a term every sentence
    # must reuse (measured: those were 100% of the noise on core).
    entity = re.compile(r'^LOC_(UNIT|BUILDING|IMPROVEMENT|TERRAIN|FEATURE|BIOME|RESOURCE|YIELD|AGE_(ANTIQUITY|EXPLORATION|MODERN)'
                        r'|PROMOTION|PROJECT|TRADITION|CIVILIZATION|LEADER|DISTRICT|WONDER|QUARTER)_')
    for row in read_tsv(os.path.join(MOD, 'glossary', 'names.tsv')):
        if len(row) >= 3 and entity.match(row[2]):
            canon.setdefault(row[0], row[1])
    terms = {en: th for en, th in canon.items()
             if len(en) >= 4 and en not in COMMON and re.search(r'[A-Za-z]', en) and th and th != en}
    pats = {en: re.compile(r'\b' + re.escape(en) + r'\b') for en in terms}

    cat = {}
    for line in open(os.path.join(MOD, 'work', 'catalog.jsonl'), encoding='utf-8'):
        u = json.loads(line)
        cat[(u['tag'], u['en_sha'])] = u['en']

    files = [os.path.join(MOD, 'translations', f'{m}.jsonl') for m in mods] if mods else \
        sorted(glob.glob(os.path.join(MOD, 'translations', '*.jsonl')))
    used, missed = Counter(), Counter()
    examples = defaultdict(list)
    rows = 0
    for path in files:
        for line in open(path, encoding='utf-8'):
            e = json.loads(line)
            en = cat.get((e['tag'], e['en_sha']))
            if en is None or e['tag'].endswith('_NAME'):
                continue
            rows += 1
            plain = MARKUP.sub(' ', en)
            for term, pat in pats.items():
                if pat.search(plain):
                    if terms[term] in e['th']:
                        used[term] += 1
                    else:
                        missed[term] += 1
                        if len(examples[term]) < 2:
                            examples[term].append(f"{e['tag']}: {e['th'][:70]}")
    print(f'{rows} translated description rows checked against {len(terms)} canonical names/terms')
    worst = sorted(missed, key=lambda t: (-missed[t] / (missed[t] + used[t]), -missed[t]))
    print('term | canonical Thai | used | not used')
    for t in worst[:40]:
        print(f'{t} | {terms[t]} | {used[t]} | {missed[t]}')
        for ex in examples[t]:
            print('    e.g.', ex)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
