#!/usr/bin/env python3
"""Phase 1, step 2: list the names that must be translated the same way everywhere.

Takes every Name="LOC_..." from the gameplay tables that hold proper nouns and core concepts,
looks up its English in work/catalog.jsonl, and counts how many catalogue strings mention it.
High-frequency terms are decided first, because every later translation depends on them.

  work/glossary-candidates.tsv   table, tag, english, mentions   (English text — never committed)

Decisions go to glossary/terms.tsv (committed): english, thai, category, status, note.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

try:
    import defusedxml.ElementTree as ET  # nosemgrep: use-defused-xml-parse
except ImportError:
    import xml.etree.ElementTree as ET  # nosemgrep: use-defused-xml

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
WORK = os.path.join(MOD, 'work')
GAME = os.environ.get(
    'CIV7_RESOURCES',
    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/"
                       "Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources"))

# Tables whose Name is a term a player meets repeatedly (measured: counts per table, 2026-11-06).
TABLES = [
    'Ages', 'Yields', 'Civilizations', 'Leaders', 'Units', 'Constructibles', 'Districts',
    'ProgressionTreeNodes', 'ProgressionTrees', 'Resources', 'Terrains', 'Features', 'Biomes',
    'Beliefs', 'Traditions', 'GreatPersonIndividuals', 'UnitPromotions', 'Victories',
    'Legacies', 'Independents', 'Governments', 'Policies', 'CityStateBonuses', 'Traits',
]
MIN_CANDIDATES = 1000  # plausibility floor for the corpus guard


def main():
    cat_path = os.path.join(WORK, 'catalog.jsonl')
    if not os.path.isfile(cat_path):
        print('COULD NOT LOOK: run tools/extract.py first')
        return 2
    en = {}
    texts = []
    for line in open(cat_path, encoding='utf-8'):
        u = json.loads(line)
        en.setdefault(u['tag'], u['en'])
        texts.append(re.sub(r'\[[^\]]*\]|\{[^}]*\}', ' ', u['en']).lower())  # drop [LI], {1_X} markup

    refs = defaultdict(set)  # tag -> {table}
    files = 0
    for root, _, names in os.walk(GAME):
        if os.sep + 'text' in root or os.sep + 'ui' in root:
            continue
        for n in names:
            if not n.endswith('.xml'):
                continue
            try:
                tree = ET.parse(os.path.join(root, n))  # nosemgrep: use-defused-xml-parse -- local game/mod files only; defusedxml used when installed
            except ET.ParseError:
                continue
            files += 1
            for table in tree.getroot():
                tname = table.tag.split('}')[-1]
                if tname not in TABLES:
                    continue
                for row in table:
                    name = row.get('Name')
                    if name and name.startswith('LOC_'):
                        refs[name].add(tname)

    rows = []
    unresolved = 0
    for tag, tables in refs.items():
        term = en.get(tag)
        if term is None:
            unresolved += 1
            continue
        term = re.sub(r'\[[^\]]*\]|\{[^}]*\}', '', term).strip()
        if not term or len(term) > 60:
            continue
        pat = re.compile(r'\b' + re.escape(term.lower()) + r'\b')
        mentions = sum(1 for t in texts if pat.search(t))
        rows.append((mentions, '/'.join(sorted(tables)), tag, term))

    if len(rows) < MIN_CANDIDATES:
        print(f'COULD NOT LOOK: only {len(rows)} candidates from {files} data files')
        return 2
    rows.sort(key=lambda r: (-r[0], r[3]))
    with open(os.path.join(WORK, 'glossary-candidates.tsv'), 'w', encoding='utf-8') as f:
        f.write('mentions\ttable\ttag\tenglish\n')
        for r in rows:
            f.write('\t'.join(map(str, r)) + '\n')
    by_table = Counter(r[1].split('/')[0] for r in rows)
    print(f'{files} data files, {len(rows)} candidate terms ({unresolved} names with no English row)')
    print('by table:', ', '.join(f'{t} {n}' for t, n in by_table.most_common(12)))
    print('most-mentioned:', ', '.join(f'{r[3]} ({r[0]})' for r in rows[:25]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
