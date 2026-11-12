#!/usr/bin/env python3
"""Build the Ayutthaya mod's text and refuse to build anything inconsistent.

  python3 tools/build.py          # check, then write text/gen/en_us.xml and text/gen/th.xml
  python3 tools/build.py --check  # check only

text/strings.txt holds every player-facing string in English and Thai. The checks:
  1. every block has both languages, and the Thai keeps the English markup ([icon:..], [TIP:..], {1_x});
  2. the Thai uses only characters the Thai Language Pack fonts draw, and no stray space beside a link;
  3. every LOC_ key the data, config and modinfo use exists: ours in strings.txt, the game's in the
     catalogue the Thai pack extracts (thai-language/work/catalog.jsonl); an unused string is a finding;
  4. every LTH type the data uses is declared in a <Types> row, every LTH modifier is defined;
  5. the modinfo lists exactly the files in data/ and config/, and every one is well-formed XML.
Each sweep prints how much it examined and fails as COULD NOT LOOK on an empty corpus.
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
REPO = os.path.dirname(MOD)
THAI_TOOLS = os.path.join(REPO, 'thai-language', 'tools')
sys.path.insert(0, THAI_TOOLS)
import lthtext  # noqa: E402  token rules shared with the Thai Language Pack
from fix_tip_spaces import fix as fix_tip_spaces  # noqa: E402

LOC = re.compile(r'\bLOC_[A-Z0-9_]+\b')
LTH_TYPE = re.compile(r'\b(?:CIVILIZATION|TRAIT|UNIT|BUILDING|QUARTER|TRADITION|TREE_CIVICS_EX|NODE_CIVIC_EX|ABILITY|UNLOCK)_LTH_[A-Z0-9_]+\b')
MODIFIER_REF = re.compile(r'\bModifierI[dD]="([A-Z0-9_]*LTH[A-Z0-9_]*)"')


def parse_strings(path):
    """{tag: {'en': str, 'th': str}} plus a list of format findings."""
    out, bad, tag, last = {}, [], None, None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith('@'):
            tag = line[1:].strip()
            if tag in out:
                bad.append(f'strings.txt:{n}: duplicate tag {tag}')
            out[tag] = {}
            last = None
        elif line.startswith('+') and tag and last:
            out[tag][last] += ' ' + line[1:].strip()
        elif tag and line[:3] in ('en:', 'th:'):
            last = line[:2]
            out[tag][last] = line[3:].strip()
        else:
            bad.append(f'strings.txt:{n}: not a tag, en:, th: or + line')
    return out, bad


def game_tags():
    path = os.path.join(REPO, 'thai-language', 'work', 'catalog.jsonl')
    if not os.path.isfile(path):
        return None
    return {json.loads(l)['tag'] for l in open(path, encoding='utf-8')}


def modinfo_items(path):
    t = open(path, encoding='utf-8').read()
    return set(re.findall(r'<Item[^>]*>([^<]+)</Item>', t))


def main(check_only):
    findings = []
    strings, bad = parse_strings(os.path.join(MOD, 'text', 'strings.txt'))
    findings += bad
    if not strings:
        print('COULD NOT LOOK: text/strings.txt holds no strings')
        return 2

    # 1-2: both languages, markup, characters, link spacing
    for tag, s in strings.items():
        en, th = s.get('en', ''), s.get('th', '')
        if not en or not th:
            findings.append(f'{tag}: missing {"en" if not en else "th"}')
            continue
        missing, extra = lthtext.compare(en, th)
        if missing or extra:
            findings.append(f'{tag}: Thai markup differs from English (missing {missing}, extra {extra})')
        if lthtext.bad_chars(th):
            findings.append(f'{tag}: characters the Thai fonts may not draw: {lthtext.bad_chars(th)}')
        if fix_tip_spaces(th) != th:
            findings.append(f'{tag}: a space between Thai and a [TIP] link')

    # 3: LOC keys used vs defined
    files = sorted(glob.glob(os.path.join(MOD, 'data', '**', '*.xml'), recursive=True)
                   + glob.glob(os.path.join(MOD, 'config', '*.xml')))
    if not files:
        print('COULD NOT LOOK: no data/config XML found')
        return 2
    used, corpus = set(), {}
    for f in files:
        rel = os.path.relpath(f, MOD)
        corpus[rel] = open(f, encoding='utf-8').read()
        try:
            ET.fromstring(corpus[rel].encode('utf-8'))
        except ET.ParseError as e:
            findings.append(f'{rel}: not well-formed XML: {e}')
        used |= set(LOC.findall(corpus[rel]))
    base = game_tags()
    for key in sorted(used):
        if key in strings:
            continue
        if 'LTH' in key:
            findings.append(f'{key}: used in data but not in strings.txt')
        elif base is None:
            pass  # reported once below
        elif key not in base:
            findings.append(f'{key}: neither ours nor a game string (check the spelling)')
    for tag in sorted(strings):
        if tag not in used and not tag.startswith('LOC_PEDIA_PAGE_'):
            findings.append(f'{tag}: in strings.txt but used nowhere')

    # 4: LTH types declared, LTH modifiers defined
    everything = '\n'.join(corpus.values())
    declared = set(re.findall(r'<(?:Row|InsertOrIgnore) Type="([A-Z0-9_]+)" Kind="KIND_', everything))
    declared |= set(re.findall(r'<Row Tag="([A-Z0-9_]+)" Category=', everything))
    for t in sorted(set(LTH_TYPE.findall(everything))):
        if t not in declared and not t.startswith('UNIT_CLASS_'):
            findings.append(f'{t}: used but never declared in a <Types> row')
    defined_mods = set(re.findall(r'<Modifier id="([A-Z0-9_]+)"', everything))
    for m in sorted(set(MODIFIER_REF.findall(everything))):
        if m not in defined_mods:
            findings.append(f'{m}: referenced as a modifier but no <Modifier id> defines it')

    # 5: modinfo lists exactly our files
    listed = modinfo_items(os.path.join(MOD, 'ayutthaya.modinfo'))
    on_disk = {os.path.relpath(f, MOD) for f in files}
    for f in sorted(on_disk - listed):
        findings.append(f'{f}: on disk but not loaded by ayutthaya.modinfo')
    for f in sorted(x for x in listed - on_disk if not x.startswith('text/gen/') and not os.path.isfile(os.path.join(MOD, x))):
        findings.append(f'{f}: listed in ayutthaya.modinfo but missing')

    print(f'examined {len(strings)} strings, {len(files)} data/config files, {len(used)} LOC keys used'
          + ('' if base is not None else ' (game catalogue missing: game keys NOT checked, run thai-language/tools/extract.py)'))
    if findings:
        print(f'{len(findings)} finding(s):')
        for f in findings:
            print('  ' + f)
        return 1
    print('0 findings')
    if check_only:
        return 0

    from build_text import segment  # pythainlp; only needed to write Thai
    os.makedirs(os.path.join(MOD, 'text', 'gen'), exist_ok=True)
    head = '<?xml version="1.0" encoding="utf-8"?>\n<!-- GENERATED by tools/build.py from text/strings.txt. Do not edit. -->\n<Database>\n'
    en = head + '\t<EnglishText>\n' + ''.join(
        f'\t\t<Row Tag="{t}"><Text>{escape(s["en"])}</Text></Row>\n' for t, s in sorted(strings.items())) + '\t</EnglishText>\n</Database>\n'
    th = head + '\t<LocalizedText>\n' + ''.join(
        f'\t\t<Replace Tag="{t}" Language="en_US"><Text>{escape(segment(s["th"]))}</Text></Replace>\n' for t, s in sorted(strings.items())) + '\t</LocalizedText>\n</Database>\n'
    for name, body in (('en_us.xml', en), ('th.xml', th)):
        with open(os.path.join(MOD, 'text', 'gen', name), 'w', encoding='utf-8') as f:
            f.write(body)
    print(f'wrote text/gen/en_us.xml and text/gen/th.xml ({len(strings)} rows each)')
    return 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv))
