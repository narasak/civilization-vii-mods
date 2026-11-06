#!/usr/bin/env python3
"""Phase 1, step 1: build the catalogue of every English string the game can show.

Reads every .modinfo under the game's Resources, follows each <UpdateText> item to its file, and
records each English row together with the LOAD CONDITION of the action group that loads it
(scope + criteria such as <AgeInUse>AGE_ANTIQUITY</AgeInUse> or <ModInUse>shawnee-tecumseh</ModInUse>).

Why the condition matters (measured 2026-11-06): 304 tags are defined in more than one module, e.g.
LOC_AGE_END_WARNING_DESC in each age. The build step must put each Thai row in a group that loads
under the same condition as the English row it replaces, or one age's translation would show in all.

Output goes to work/ (git-ignored): it contains the game's English text, which is Firaxis' content
and is never committed or shipped. Translation files store only tag + English hash + Thai.

  work/catalog.jsonl   one line per unit = (tag, distinct English text)
  work/summary.json    counts, skipped items, overlapping-condition tags
"""
import hashlib
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
MIN_ROWS = 40000  # measured 44,199 Row elements on build 1.5.0 (1311346)


def strip_ns(tag):
    return tag.split('}')[-1]


def en_sha(text):
    return hashlib.sha1((text or '').encode('utf-8')).hexdigest()[:12]


def criteria_signature(crit_el):
    """Canonical, comparable form of a <Criteria> element: 'AgeInUse=AGE_ANTIQUITY' etc."""
    if crit_el is None:
        return 'MISSING'
    parts = []
    for c in crit_el:
        name = strip_ns(c.tag)
        attrs = ','.join(f'{k}={v}' for k, v in sorted(c.attrib.items()))
        parts.append(f'{name}={(c.text or "").strip()}' + (f'[{attrs}]' if attrs else ''))
    head = ','.join(f'{k}={v}' for k, v in sorted(crit_el.attrib.items()) if k != 'id')
    return (f'{{{head}}}' if head else '') + '&'.join(sorted(parts)) or 'AlwaysMet='


def load_modinfos():
    """Yield (modinfo_path, mod_id, group_id, scope, criteria_sig, item_rel, item_attrs)."""
    for root, _, names in os.walk(GAME):
        for n in names:
            if not n.endswith('.modinfo'):
                continue
            path = os.path.join(root, n)
            try:
                tree = ET.parse(path)  # nosemgrep: use-defused-xml-parse -- local game/mod files only; defusedxml used when installed
            except ET.ParseError as e:
                yield ('PARSE_ERROR', path, str(e), None, None, None, None)
                continue
            mod = tree.getroot()
            mod_id = mod.get('id')
            crits = {}
            for el in mod.iter():
                if strip_ns(el.tag) == 'Criteria' and el.get('id'):
                    crits[el.get('id')] = el
            for grp in mod.iter():
                if strip_ns(grp.tag) != 'ActionGroup':
                    continue
                scope = grp.get('scope')
                sig = criteria_signature(crits.get(grp.get('criteria')))
                for act in grp.iter():
                    if strip_ns(act.tag) != 'UpdateText':
                        continue
                    for item in act:
                        if strip_ns(item.tag) == 'Item' and item.text:
                            yield (path, mod_id, grp.get('id'), scope, sig, item.text.strip(), dict(item.attrib))


def main():
    if not os.path.isdir(GAME):
        print(f'COULD NOT LOOK: {GAME}')
        return 2
    units = {}                       # (tag, sha) -> unit
    by_tag = defaultdict(set)        # tag -> {sha}
    skipped = Counter()
    deletes = []
    files_read = set()
    rows_read = 0
    modinfos = set()

    seq = 0  # load sequence: within one condition, a later file's row wins (LOC_UI_VICTORY_PROGRESS)
    for rec in load_modinfos():
        if rec[0] == 'PARSE_ERROR':
            print(f'COULD NOT LOOK: modinfo does not parse: {rec[1]}: {rec[2]}')
            return 2
        path, mod_id, group, scope, sig, item, attrs = rec
        modinfos.add(path)
        # Item attributes gate WHERE a file loads. This Steam/macOS build loads only un-gated items:
        # locale= (other languages), platform= (consoles, iOS), ecosystem="game-center" (Apple
        # Arcade — its files Delete 90 rows). An attribute we have never seen could be a gate that
        # DOES apply here, so it stops the run instead of being guessed at.
        known_gates = ('locale', 'platform', 'ecosystem')
        unknown = [k for k in attrs if k not in known_gates]
        if unknown:
            print(f'COULD NOT LOOK: unknown item attribute(s) {unknown} on {item} in {path}')
            return 2
        gate = next((k for k in known_gates if k in attrs), None)
        if gate:
            skipped[f'{gate}={attrs[gate]}' if gate != 'locale' else 'other-locale item'] += 1
            continue
        fpath = os.path.normpath(os.path.join(os.path.dirname(path), item))
        if not fpath.endswith('.xml'):
            skipped['non-xml text item'] += 1
            continue
        if not os.path.isfile(fpath):
            skipped['item file missing'] += 1
            continue
        files_read.add(fpath)
        seq += 1
        rel = os.path.relpath(fpath, GAME)
        cond = {'scope': scope, 'criteria': sig}
        for table in ET.parse(fpath).getroot():  # nosemgrep: use-defused-xml-parse -- local game/mod files only; defusedxml used when installed
            for row in table:
                kind = strip_ns(row.tag)
                tag = row.get('Tag') or row.get('tag')
                if not tag:
                    continue
                lang = row.get('Language')
                if lang and lang != 'en_US':
                    continue
                if kind == 'Delete':
                    deletes.append({'tag': tag, 'file': rel, **cond})
                    continue
                if kind not in ('Row', 'Replace'):
                    continue
                rows_read += 1
                t = row.find('Text')
                text = (t.text if t is not None else row.get('Text')) or ''
                g = row.find('Gender')
                p = row.find('Plurality')
                sha = en_sha(text)
                key = (tag, sha)
                u = units.get(key)
                if u is None:
                    u = units[key] = {
                        'tag': tag, 'en_sha': sha, 'en': text,
                        'gender': g.text if g is not None else None,
                        'plurality': p.text if p is not None else None,
                        'words': len(re.sub(r'\{[^}]*\}|\[[^\]]*\]', ' ', text).split()),
                        'module': mod_id, 'sources': [],
                    }
                src = {'mod': mod_id, 'group': group, 'file': rel, **cond}
                if not any(all(x[k] == src[k] for k in src) for x in u['sources']):
                    u['sources'].append({**src, 'seq': seq})
                by_tag[tag].add(sha)

    if rows_read < MIN_ROWS:
        print(f'COULD NOT LOOK: only {rows_read} English rows read from {len(files_read)} files '
              f'(expected >= {MIN_ROWS})')
        return 2

    # Tags whose English differs between sources, and whether two variants can be live at once
    # (one 'always' + one conditional, or two conditionals sharing a scope with the same criteria).
    multi = {t: s for t, s in by_tag.items() if len(s) > 1}
    overlapping = []
    for tag, shas in multi.items():
        conds = []
        for sha in shas:
            for src in units[(tag, sha)]['sources']:
                conds.append((src['scope'], src['criteria'], sha))
        for i, a in enumerate(conds):
            for b in conds[i + 1:]:
                if a[2] != b[2] and a[0] == b[0] and ('AlwaysMet=' in (a[1], b[1]) or a[1] == b[1]):
                    overlapping.append(tag)
                    break
            else:
                continue
            break

    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, 'catalog.jsonl'), 'w', encoding='utf-8') as f:
        for key in sorted(units):
            f.write(json.dumps(units[key], ensure_ascii=False) + '\n')

    per_module = Counter()
    words_module = Counter()
    for u in units.values():
        per_module[u['module']] += 1
        words_module[u['module']] += u['words']
    summary = {
        'game': GAME,
        'modinfos': len(modinfos),
        'text_files_read': len(files_read),
        'english_rows_read': rows_read,
        'units': len(units),
        'unique_tags': len(by_tag),
        'words': sum(u['words'] for u in units.values()),
        'tags_with_variant_text': len(multi),
        'tags_with_overlapping_variants': sorted(overlapping),
        'deletes': deletes,
        'skipped_items': dict(skipped),
        'units_by_module': dict(per_module.most_common()),
        'words_by_module': dict(words_module.most_common()),
    }
    with open(os.path.join(WORK, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    print(f"examined {len(modinfos)} modinfos, {len(files_read)} text files, {rows_read} English rows")
    print(f"units {len(units)} | unique tags {len(by_tag)} | words {summary['words']}")
    print(f"tags with per-condition variant text: {len(multi)} | of those, possibly live at once: {len(overlapping)}")
    print(f"skipped items: {dict(skipped)} | Delete rows kept for build: {len(deletes)}")
    print('top modules by words:', ', '.join(f'{m} {w}' for m, w in words_module.most_common(8)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
