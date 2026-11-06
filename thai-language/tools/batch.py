#!/usr/bin/env python3
"""Split untranslated catalogue units into batches, validate translated batches, merge them.

  tools/batch.py export <module> <n_batches> [--files A.xml,B.xml] [--tags REGEX] [--exclude-tags REGEX]
                                               [--name PREFIX] [--words N  (word-balanced; ignores n_batches)]
                                               -> work/batches/<PREFIX>-NN.jsonl   (tag, en_sha, en)
  tools/batch.py names [<out.tsv>]             -> glossary/names.tsv from translated *_NAME rows
  tools/batch.py validate <in.jsonl> <out.jsonl>   exit 0 only if the output is mergeable
  tools/batch.py merge <module> <out.jsonl>...     -> translations/<module>.jsonl (status "draft")

A translated batch line is {"tag", "en_sha", "th"}. Validation applies the same rules as
tools/check.py and tools/build_text.py, so a batch that validates will build:
  * every input unit present exactly once, nothing extra, en_sha unchanged
  * placeholders / markup identical as a multiset: {1_Name} [ICON_GOLD] [N] [B] [/B] ...
  * no U+200B (the build inserts it), only ASCII + Thai block characters
  * not left in English when the English has words to translate (warn only: some are names)
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
WORK = os.path.join(MOD, 'work')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lthtext  # noqa: E402  one copy of the token rules, shared with check.py and build_text.py

# Files whose rows must stay as the game ships them.
SKIP_FILES = ('LanguageText.xml', 'GrammarText.xml')


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]


def export(module, n, files=None, tag_re=None, prefix=None, words=None, exclude_tags=None):
    BASE = {'core', 'base-standard', 'age-antiquity', 'age-exploration', 'age-modern'}
    catalog = load_jsonl(os.path.join(WORK, 'catalog.jsonl'))
    all_mods = {u['module'] for u in catalog}
    mods = (all_mods - BASE) if module == 'DLC' else set(module.split(','))
    done = set()
    for tpath in __import__('glob').glob(os.path.join(MOD, 'translations', '*.jsonl')):
        done |= {(e['tag'], e['en_sha']) for e in load_jsonl(tpath)}
    units = []
    skipped = Counter()
    for u in catalog:
        if u['module'] not in mods or (u['tag'], u['en_sha']) in done:
            continue
        f = u['sources'][0]['file'].rsplit('/', 1)[-1]
        if files and f not in files:
            continue
        if tag_re and not re.search(tag_re, u['tag']):
            continue
        if exclude_tags and re.search(exclude_tags, u['tag']):
            continue
        if f in SKIP_FILES:
            skipped[f] += 1
            continue
        if not u['en'].strip():
            skipped['empty English'] += 1
            continue
        units.append({'tag': u['tag'], 'en_sha': u['en_sha'], 'en': u['en'], 'file': f})
    units.sort(key=lambda x: (x['file'], x['tag']))  # keep a screen's strings together
    out_dir = os.path.join(WORK, 'batches')
    os.makedirs(out_dir, exist_ok=True)
    if words:  # word-balanced: one Civilopedia article weighs ~90 words, a name 2-3
        chunks, cur, cw = [], [], 0
        for x in units:
            w = len(x['en'].split())
            if cur and cw + w > words:
                chunks.append(cur)
                cur, cw = [], 0
            cur.append(x)
            cw += w
        if cur:
            chunks.append(cur)
        n = len(chunks)
    else:
        size = -(-len(units) // n)
        chunks = [units[i * size:(i + 1) * size] for i in range(n)]
    for i in range(n):
        chunk = chunks[i]
        if not chunk:
            continue
        with open(os.path.join(out_dir, f'{prefix or module}-{i + 1:02d}.jsonl'), 'w', encoding='utf-8') as f:  # noqa
            for x in chunk:
                f.write(json.dumps(x, ensure_ascii=False) + '\n')
        print(f'{prefix or module}-{i + 1:02d}.jsonl: {len(chunk)} units, '
              f'{sum(len(x["en"].split()) for x in chunk)} words')
    print(f'exported {len(units)} units; skipped {dict(skipped)}')
    return 0


def validate(inp, out, quiet=False):
    src = {(u['tag'], u['en_sha']): u for u in load_jsonl(inp)}
    try:
        res = load_jsonl(out)
    except (OSError, json.JSONDecodeError) as e:
        print(f'INVALID: {out}: {e}')
        return 1
    errors, warns = [], []
    seen = Counter((r.get('tag'), r.get('en_sha')) for r in res)
    for k, n in seen.items():
        if k not in src:
            errors.append(f'{k[0]}: not in the input batch (or en_sha changed)')
        if n > 1:
            errors.append(f'{k[0]}: appears {n} times')
    for k in src:
        if k not in seen:
            errors.append(f'{k[0]}: missing from output')
    for r in res:
        k = (r.get('tag'), r.get('en_sha'))
        if k not in src:
            continue
        th, en = r.get('th') or '', src[k]['en']
        if not th.strip():
            errors.append(f'{k[0]}: empty translation')
            continue
        if '\u200b' in th:
            errors.append(f'{k[0]}: contains U+200B (the build inserts it)')
        bad = [c for c in lthtext.bad_chars(th) if c not in lthtext.ALLOWED_EXTRA]
        if bad:
            errors.append(f'{k[0]}: characters the fonts lack: ' + ' '.join(f'U+{ord(c):04X} {c!r}' for c in bad))
        # Latin letters touching Thai with no space ("การแofficial") are corruption, not style: Thai
        # sets Latin words off with spaces. Measured: 0 such cases in 1,805 good rows. Placeholders removed first.
        glued = lthtext.glued(th)
        if glued:
            errors.append(f'{k[0]}: Latin letters glued inside Thai text: {glued[:3]}')
        missing, extra = lthtext.compare(en, th)
        if missing or extra:
            errors.append(f'{k[0]}: placeholders differ — missing {missing} extra {extra}')
        if th == en and re.search(r'[a-z]{3,}', lthtext.strip_tokens(en, '')):
            warns.append(f'{k[0]}: left in English: {en[:60]!r}')
    if not quiet:
        for e in errors:
            print('ERROR:', e)
        for w in warns[:40]:
            print('WARN:', w)
    print(f'{os.path.basename(out)}: {len(res)}/{len(src)} rows, {len(errors)} error(s), {len(warns)} untranslated-looking')
    return 1 if errors else 0


def merge(module, outs):
    """Validate each batch, then file every row under translations/<its catalogue module>.jsonl.
    (`module` is ignored: one batch may mix modules, e.g. all DLC names.)"""
    owner = {(u['tag'], u['en_sha']): u['module'] for u in load_jsonl(os.path.join(WORK, 'catalog.jsonl'))}
    for out in outs:
        inp = re.sub(r'\.th\.jsonl$', '.jsonl', out)
        if validate(inp, out, quiet=True) != 0:
            print(f'REFUSED: {out} does not validate; run: tools/batch.py validate {inp} {out}')
            return 1
    stores, have = {}, set()
    for path in __import__('glob').glob(os.path.join(MOD, 'translations', '*.jsonl')):
        m = os.path.basename(path)[:-6]
        stores[m] = load_jsonl(path)
        have |= {(e['tag'], e['en_sha']) for e in stores[m]}
    added = Counter()
    for out in outs:
        for r in load_jsonl(out):
            k = (r['tag'], r['en_sha'])
            if k in have:
                continue
            m = owner[k]
            stores.setdefault(m, []).append({'tag': r['tag'], 'en_sha': r['en_sha'], 'status': 'draft', 'th': r['th']})
            have.add(k)
            added[m] += 1
    for m in added:
        rows = sorted(stores[m], key=lambda e: e['tag'])
        with open(os.path.join(MOD, 'translations', f'{m}.jsonl'), 'w', encoding='utf-8') as f:
            for e in rows:
                f.write(json.dumps(e, ensure_ascii=False) + '\n')
    total = sum(added.values())
    print(f'merged {total} new draft row(s): ' + (', '.join(f'{m} {n}' for m, n in added.most_common()) or 'nothing new'))
    return 0

def names():
    """glossary/names.tsv: every translated *_NAME row — the spelling every later batch must reuse."""
    cat = {(u['tag'], u['en_sha']): u['en'] for u in load_jsonl(os.path.join(WORK, 'catalog.jsonl'))}
    rows = []
    for path in sorted(__import__('glob').glob(os.path.join(MOD, 'translations', '*.jsonl'))):
        for e in load_jsonl(path):
            en = cat.get((e['tag'], e['en_sha']))
            if en and e['tag'].endswith('_NAME') and len(en) <= 60 and '\n' not in en:
                rows.append((en.strip(), e['th'], e['tag']))
    rows.sort(key=lambda r: r[0].lower())
    out = os.path.join(MOD, 'glossary', 'names.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('english\tthai\ttag\n')
        for r in rows:
            f.write('\t'.join(r) + '\n')
    clash = Counter(r[0] for r in rows)
    # glossary/homonyms.tsv: English words that legitimately name different things (Marine: biome vs unit).
    hpath = os.path.join(MOD, 'glossary', 'homonyms.tsv')
    homonyms = {l.split('\t')[0] for l in open(hpath, encoding='utf-8').read().splitlines()[1:]} if os.path.isfile(hpath) else set()
    multi = {k for k, v in clash.items() if v > 1 and k not in homonyms and len({r[1] for r in rows if r[0] == k}) > 1}
    print(f'glossary/names.tsv: {len(rows)} names; same English, different Thai: {sorted(multi)[:20]}')
    return 1 if multi else 0


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['export'] and len(a) >= 3:
        opt = dict(zip(a[3::2], a[4::2]))
        sys.exit(export(a[1], int(a[2]),
                        files=set(opt['--files'].split(',')) if '--files' in opt else None,
                        tag_re=opt.get('--tags'), prefix=opt.get('--name'),
                        words=int(opt['--words']) if '--words' in opt else None,
                        exclude_tags=opt.get('--exclude-tags')))
    if a[:1] == ['names']:
        sys.exit(names())
    if a[:1] == ['validate'] and len(a) == 3:
        sys.exit(validate(a[1], a[2]))
    if a[:1] == ['merge'] and len(a) >= 3:
        sys.exit(merge(a[1], a[2:]))
    print(__doc__)
    sys.exit(2)
