#!/usr/bin/env python3
"""Phase 1, step 3: turn translations/*.jsonl into the mod's text files and modinfo text groups.

Store format (translations/<module>.jsonl, one JSON object per line, committed):
    {"tag": "LOC_...", "en_sha": "<12 hex>", "status": "draft"|"reviewed", "th": "<clean Thai>"}
`th` holds NO zero-width spaces: this script inserts U+200B between Thai words (PyThaiNLP newmm)
in strings of 20+ visible characters, never inside {placeholders} or [markup], never in short labels
(letter-spaced menus draw each U+200B as a gap — measured on the main menu 2026-11-06).

Placement: every catalogue unit lists the load conditions (scope + criteria) of the English row it
replaces. Each Thai row is emitted once per condition, into an action group with the same criteria,
so an age-specific English string gets its Thai only in that age. Where two English variants of one
tag are live under one condition, the game shows the later-loaded one; we translate only that one.

Outputs (generated, do not hand-edit): text/gen/*.xml and the block between the LTH:GENERATED markers
in thai-language.modinfo. Requires: pip install -r tools/requirements.txt
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict
from xml.sax.saxutils import escape

try:
    from pythainlp.tokenize import word_tokenize
except ImportError:
    print('COULD NOT LOOK: pythainlp missing — pip install -r tools/requirements.txt')
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
WORK = os.path.join(MOD, 'work')
GEN = os.path.join(MOD, 'text', 'gen')
MODINFO = os.path.join(MOD, 'thai-language.modinfo')
BEGIN, END = '<!-- LTH:GENERATED BEGIN -->', '<!-- LTH:GENERATED END -->'
CBEGIN, CEND = '<!-- LTH:CRITERIA BEGIN -->', '<!-- LTH:CRITERIA END -->'
ZWSP = '\u200b'
SHORT = 20
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lthtext  # noqa: E402  shared token rules (nested selectors kept whole)
THAI = re.compile(r'[\u0e00-\u0e7f]')
STATUSES = ('draft', 'reviewed')


def visible_len(s):
    return len(lthtext.strip_tokens(s, ''))


def segment(th):
    """Insert U+200B between adjacent Thai words; markup tokens and non-Thai text are untouched."""
    if ZWSP in th:
        raise ValueError('stored Thai must not contain U+200B; the build inserts it')
    if visible_len(th) < SHORT:
        return th
    out = []
    for piece in lthtext.split_keep(th):
        if not piece or lthtext.is_token(piece) or not THAI.search(piece):
            out.append(piece)
            continue
        words = word_tokenize(piece, engine='newmm', keep_whitespace=True)
        buf = ''
        for i, w in enumerate(words):
            if i and THAI.search(w[:1]) and THAI.search(words[i - 1][-1:]):
                buf += ZWSP
            buf += w
        out.append(buf)
    return ''.join(out)


def criteria_xml(sig, cid):
    head = {}
    m = re.match(r'^\{([^}]*)\}(.*)$', sig)
    if m:
        head = dict(kv.split('=', 1) for kv in m.group(1).split(',') if kv)
        sig = m.group(2)
    attrs = ''.join(f' {k}="{escape(v)}"' for k, v in head.items())
    kids = []
    for part in sig.split('&'):
        name, _, val = part.partition('=')
        val = re.sub(r'\[.*\]$', '', val)
        kids.append(f'\t\t\t<{name}>{escape(val)}</{name}>' if val else f'\t\t\t<{name}></{name}>')
    return f'\t\t<Criteria id="{cid}"{attrs}>\n' + '\n'.join(kids) + '\n\t\t</Criteria>'


def main():
    cat_path = os.path.join(WORK, 'catalog.jsonl')
    if not os.path.isfile(cat_path):
        print('COULD NOT LOOK: run tools/extract.py first')
        return 2
    units = {}
    variants = defaultdict(list)
    for line in open(cat_path, encoding='utf-8'):
        u = json.loads(line)
        units[(u['tag'], u['en_sha'])] = u
        variants[u['tag']].append(u)

    # Which variant wins under each condition: the highest load sequence.
    winner = {}
    for tag, us in variants.items():
        best = {}
        for u in us:
            for s in u['sources']:
                c = (s['scope'], s['criteria'])
                if c not in best or s['seq'] > best[c][0]:
                    best[c] = (s['seq'], u['en_sha'])
        for c, (_, sha) in best.items():
            winner[(tag, c)] = sha

    files = sorted(glob.glob(os.path.join(MOD, 'translations', '*.jsonl')))
    by_cond = defaultdict(list)
    stats = defaultdict(int)
    problems = []
    seen = set()
    for path in files:
        rel = os.path.relpath(path, MOD)
        for n, line in enumerate(open(path, encoding='utf-8'), 1):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError as ex:
                problems.append(f'{rel}:{n}: not JSON: {ex}')
                continue
            key = (e.get('tag'), e.get('en_sha'))
            if key in seen:
                problems.append(f'{rel}:{n}: duplicate entry {key}')
                continue
            seen.add(key)
            if e.get('status') not in STATUSES:
                stats['skipped:' + str(e.get('status'))] += 1
                continue
            u = units.get(key)
            if u is None:
                cur = [v['en_sha'] for v in variants.get(e.get('tag'), [])]
                problems.append(f'{rel}:{n}: {e.get("tag")} is STALE — English changed '
                                f'(stored {e.get("en_sha")}, game now {cur or "no such tag"})')
                continue
            try:
                # Names are titles on one line, often in letter-spaced styles (Tech Tree, unit panel),
                # where each U+200B draws a visible gap: never segment them, whatever their length.
                th = e['th'] if e['tag'].endswith('_NAME') else segment(e['th'])
            except ValueError as ex:
                problems.append(f'{rel}:{n}: {e["tag"]}: {ex}')
                continue
            for s in u['sources']:
                c = (s['scope'], s['criteria'])
                if winner.get((e['tag'], c)) != u['en_sha']:
                    stats['shadowed variant'] += 1
                    continue
                by_cond[c].append((e['tag'], th, u.get('gender'), u.get('plurality')))
            stats[e['status']] += 1

    if problems:
        for p in problems:
            print('PROBLEM:', p)
        print(f'{len(problems)} problem(s); nothing written')
        return 1

    os.makedirs(GEN, exist_ok=True)
    for old in glob.glob(os.path.join(GEN, '*.xml')):
        os.remove(old)
    conds = sorted(by_cond)
    groups, crits, rows_out = [], [], 0
    for i, (scope, sig) in enumerate(conds, 1):
        rows = sorted(set(by_cond[(scope, sig)]))
        name = f'{i:02d}-{scope}.xml'
        with open(os.path.join(GEN, name), 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n<!-- GENERATED by tools/build_text.py from '
                    'translations/*.jsonl. Do not edit. -->\n'
                    f'<!-- condition: scope={scope} criteria={escape(sig)} -->\n<Database>\n\t<LocalizedText>\n')
            for tag, th, gender, plur in rows:
                extra = (f'<Gender>{escape(gender)}</Gender>' if gender else '') + \
                        (f'<Plurality>{escape(plur)}</Plurality>' if plur else '')
                f.write(f'\t\t<Replace Tag="{escape(tag)}" Language="en_US"><Text>{escape(th)}</Text>{extra}</Replace>\n')
            f.write('\t</LocalizedText>\n</Database>\n')
        rows_out += len(rows)
        cid = f'lth-cond-{i:02d}'
        crits.append(criteria_xml(sig, cid))
        groups.append(f'\t\t<ActionGroup id="lth-text-{i:02d}" scope="{scope}" criteria="{cid}">\n'
                      '\t\t\t<Properties><LoadOrder>1000</LoadOrder></Properties>\n'
                      f'\t\t\t<Actions><UpdateText><Item>text/gen/{name}</Item></UpdateText></Actions>\n'
                      '\t\t</ActionGroup>')

    mi = open(MODINFO, encoding='utf-8').read()
    for b, e, body in ((BEGIN, END, '\n'.join(groups)), (CBEGIN, CEND, '\n'.join(crits))):
        if b not in mi or e not in mi:
            print(f'COULD NOT LOOK: markers {b} … {e} missing from thai-language.modinfo')
            return 2
        mi = re.sub(re.escape(b) + r'.*?' + re.escape(e), lambda _: f'{b}\n{body}\n\t\t{e}', mi, flags=re.S)
    open(MODINFO, 'w', encoding='utf-8').write(mi)

    print(f'{len(files)} translation file(s): ' + ', '.join(f'{k} {v}' for k, v in sorted(stats.items())))
    print(f'wrote {rows_out} rows into {len(conds)} condition group(s): ' +
          ', '.join(f'{s}/{c}' for s, c in conds))
    return 0


if __name__ == '__main__':
    sys.exit(main())
