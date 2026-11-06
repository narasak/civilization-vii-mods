#!/usr/bin/env python3
"""Gate for the Thai mod. Exit 0 = clean, 1 = findings, 2 = could not look.

Checks:
  1. Every file the modinfo names exists.
  2. Every XML file parses.
  3. Every <Replace Tag=...> names a tag that exists in the game's en_US text (a typo'd tag is a
     row the game never reads — silently untranslated).
  4. Every translated row carries exactly the same placeholders as the English row:
     {1_GameName}-style substitutions and [B] [N] [ICON_x] style markup. A dropped {n} renders
     blank; an extra one renders the literal braces.

The en_US corpus size is printed and must be plausible, so "0 findings" can never mean "read
nothing" (measured 2026-11-06: 44,193 rows across Base + DLC).
"""
import glob
import json
import os
import re
import sys
from collections import Counter

# Inputs are this mod's own files and the locally installed game's text — not untrusted input —
# and Python >= 3.7.1 does not resolve external entities by default. Still prefer defusedxml
# (XXE / entity-expansion hardened) when it is installed; fall back so the gate needs no pip.
try:
    import defusedxml.ElementTree as ET  # nosemgrep: use-defused-xml-parse
    XML_PARSER = 'defusedxml'
except ImportError:
    import xml.etree.ElementTree as ET  # nosemgrep: use-defused-xml
    XML_PARSER = 'stdlib xml.etree (pip install defusedxml to harden)'

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
GAME = os.environ.get(
    'CIV7_RESOURCES',
    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/"
                       "Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources"))
MIN_EN_ROWS = 40000  # measured 44,193; below this the corpus was not read properly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lthtext  # noqa: E402  shared with batch.py and build_text.py
import fix_tip_spaces  # noqa: E402  the same patterns the fixer removes


def load_english():
    """English variants per tag, from work/catalog.jsonl — the SAME source the build and the batch
    validator read. This used to walk the XML itself and read platform-gated files (Xbox, Switch,
    Apple Arcade) too, so it compared a translation against an English string this build never
    loads (LOC_GESTURE_THUMB_AXIS, 2026-11-06). A check and the action it guards must read one value."""
    path = os.path.join(MOD, 'work', 'catalog.jsonl')
    rows = {}
    if not os.path.isfile(path):
        return None, 0
    n = 0
    for line in open(path, encoding='utf-8'):
        u = json.loads(line)
        rows.setdefault(u['tag'], []).append(u['en'])
        n += 1
    return rows, n


def main():
    if not os.path.isdir(GAME):
        print(f'COULD NOT LOOK: game resources not found at {GAME} (set CIV7_RESOURCES)')
        return 2
    findings = []

    modinfo = os.path.join(MOD, 'thai-language.modinfo')
    try:
        mtree = ET.parse(modinfo)  # nosemgrep: use-defused-xml-parse -- local game/mod files only; defusedxml used when installed
    except (OSError, ET.ParseError) as e:
        print(f'COULD NOT LOOK: modinfo unreadable: {e}')
        return 2
    # Metadata is drawn on the Add-Ons screen, where our Thai font is not loaded: Thai there shows as
    # empty boxes. (Once blamed for a crash on quit; a control run with NO third-party mods (2026-11-06 08:28) crashed identically, so the crash is not ours.)
    for el in mtree.iter():
        name = el.tag.split('}')[-1]
        if name in ('Name', 'Description', 'Authors') and el.text and not el.text.isascii():
            findings.append(f'modinfo <{name}> contains non-ASCII text: {el.text.strip()!r}')
    root = mtree.getroot()
    if not (root.get('version') or '').isdigit():
        findings.append(f'modinfo version must be an integer (Mods.Version is INTEGER), got {root.get("version")!r}')

    items = [el.text.strip() for el in mtree.iter() if el.tag.endswith('Item') and el.text]
    for it in sorted(set(items)):
        if not os.path.isfile(os.path.join(MOD, it)):
            findings.append(f'modinfo names a missing file: {it}')

    english, en_files = load_english()
    if english is None:
        print('COULD NOT LOOK: work/catalog.jsonl missing — run tools/extract.py')
        return 2
    if len(english) < MIN_EN_ROWS:
        print(f'COULD NOT LOOK: read only {len(english)} tags ({en_files} catalogue units) '
              f'(expected >= {MIN_EN_ROWS})')
        return 2

    checked = 0
    text_files = sorted({it for it in items if it.startswith('text/') and it.endswith('.xml')})
    for rel in text_files:
        path = os.path.join(MOD, rel)
        try:
            tree = ET.parse(path)  # nosemgrep: use-defused-xml-parse -- local game/mod files only; defusedxml used when installed
        except (OSError, ET.ParseError) as e:
            findings.append(f'{rel}: does not parse: {e}')
            continue
        for el in tree.iter('Replace'):
            tag = el.get('Tag')
            checked += 1
            t = el.find('Text')
            thai = t.text if t is not None else ''
            if el.get('Language') != 'en_US':
                findings.append(f'{rel}: {tag}: Language must be en_US (Thai is not a selectable locale)')
            if tag not in english:
                findings.append(f'{rel}: {tag}: no such tag in the game\'s en_US text')
                continue
            # A character no loaded font covers renders blank. Allow only characters our fonts are
            # built to cover: ASCII, the Thai block, and the zero-width set added by
            # tools/build-fonts.py.
            bad = lthtext.bad_chars(thai)
            if bad:
                findings.append(f'{rel}: {tag}: characters no bundled font is known to cover: '
                                + ' '.join(f'U+{ord(c):04X}' for c in bad))
            # Short labels sit in letter-spaced menus, where each U+200B draws one tracking gap.
            visible = lthtext.strip_tokens((thai or '').replace('\u200b', ''), '')
            if '\u200b' in (thai or '') and tag.endswith('_NAME'):
                findings.append(f'{rel}: {tag}: U+200B in a name — names sit in letter-spaced titles '
                                '(Tech Tree, unit panel) where it renders as a visible gap')
            elif '\u200b' in (thai or '') and len(visible) < 20:
                findings.append(f'{rel}: {tag}: U+200B in a short label ({len(visible)} chars) — '
                                'letter-spaced menus render it as a visible gap')
            if fix_tip_spaces.count((thai or '').replace('\u200b', '')):
                findings.append(f'{rel}: {tag}: space between Thai and a [TIP] link — run tools/fix_tip_spaces.py')
            glued = lthtext.glued(thai)
            if glued:
                findings.append(f'{rel}: {tag}: Latin letters touching Thai with no space: {glued[:3]}')
            results = [lthtext.compare(v, thai) for v in english[tag]]
            missing, extra = next((r for r in results if r == ([], [])), results[0])
            if missing or extra:
                findings.append(f'{rel}: {tag}: placeholders differ — missing {missing} extra {extra}')

    # Font-stack coverage: every place the GAME sets a BodyFont/TitleFont stack must be out-ranked by
    # ui/lth-thai-fonts.js, or Thai there renders with no Thai font -> blank text.
    js_path = os.path.join(MOD, 'ui', 'lth-thai-fonts.js')
    try:
        js = open(js_path, encoding='utf-8').read()
    except OSError as e:
        print(f'COULD NOT LOOK: {js_path}: {e}')
        return 2
    static_sel = set()
    css_files = 0
    for root, _, names in os.walk(GAME):
        for n in names:
            if not n.endswith('.css'):
                continue
            css_files += 1
            css = re.sub(r'/\*.*?\*/', '', open(os.path.join(root, n), errors='ignore').read(), flags=re.S)
            for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
                if re.search(r'font-family\s*:[^;]*(BodyFont|TitleFont)', m.group(2)):
                    for sel in m.group(1).split(','):
                        static_sel.add(' '.join(sel.split()))
    gs_path = os.path.join(GAME, 'Base/modules/core/ui/themes/default/global-scaling.js')
    try:
        gs = open(gs_path, encoding='utf-8').read()
    except OSError as e:
        print(f'COULD NOT LOOK: {gs_path}: {e}')
        return 2
    sizes = re.findall(r'\{\s*name:\s*"([^"]+)",\s*px:', gs)
    if css_files < 100 or not static_sel or not sizes:
        print(f'COULD NOT LOOK: font-rule inventory implausible ({css_files} css files, '
              f'{len(static_sel)} static selectors, {len(sizes)} sizes)')
        return 2
    for sel in sorted(static_sel):
        if f"'{sel}'" not in js:
            findings.append(f'game CSS sets a font stack on "{sel}" but ui/lth-thai-fonts.js does not override it')
    js_sizes = re.search(r"const SIZES = \[([^\]]*)\]", js)
    have = set(re.findall(r"'([^']+)'", js_sizes.group(1))) if js_sizes else set()
    for z in sizes:
        if z not in have:
            findings.append(f'global-scaling.js generates .font-*-{z} but SIZES in ui/lth-thai-fonts.js lacks it')
    print(f'font rules: {len(static_sel)} static selectors in {css_files} css files, '
          f'{len(sizes)} generated sizes — all must be overridden')

    # Early stylesheet copies (tools/build_css.py) replace a game file. They must be the game's
    # CURRENT bytes plus our block — a copy of an older original would silently undo a game update.
    orig_css = os.path.join(GAME, 'Base', 'modules', 'core', 'ui', 'themes', 'default', 'panel-animations.css')
    for rel in ('core/ui/themes/default/panel-animations.css',):
        p = os.path.join(MOD, rel)
        if not os.path.isfile(p):
            continue
        if not os.path.isfile(orig_css):
            print(f'COULD NOT LOOK: {orig_css}')
            return 2
        if not open(p, 'rb').read().startswith(open(orig_css, 'rb').read()):
            findings.append(f'{rel}: does not start with the game\'s current panel-animations.css — run tools/build_css.py')

    # Source files must not hold invisible characters literally: an editor shows nothing, review
    # cannot see them, and the Write tool turned backslash-u escapes into real ones twice (2026-11-06).
    invisible = {0x200b, 0x200c, 0x200d, 0x2060, 0xfeff}
    for src_path in sorted(glob.glob(os.path.join(MOD, 'tools', '*.py')) + glob.glob(os.path.join(MOD, 'ui', '*.js'))):
        for n, line in enumerate(open(src_path, encoding='utf-8'), 1):
            if any(ord(c) in invisible for c in line):
                findings.append(f'{os.path.relpath(src_path, MOD)}:{n}: literal invisible character — write it as an escape')

    # Glossary shape: one decision per English term, a known status, Thai the fonts can draw.
    gpath = os.path.join(MOD, 'glossary', 'terms.tsv')
    if os.path.isfile(gpath):
        seen_terms = {}
        lines = open(gpath, encoding='utf-8').read().splitlines()
        if not lines or lines[0].split('\t')[:4] != ['english', 'thai', 'category', 'status']:
            findings.append('glossary/terms.tsv: header must start english, thai, category, status')
        for n, line in enumerate(lines[1:], 2):
            cols = line.split('\t')
            if len(cols) < 4:
                findings.append(f'glossary/terms.tsv:{n}: needs at least 4 tab-separated columns')
                continue
            en_term, th_term, _, status = cols[:4]
            if en_term in seen_terms:
                findings.append(f'glossary/terms.tsv:{n}: "{en_term}" already decided on line {seen_terms[en_term]}')
            seen_terms[en_term] = n
            if status not in ('proposed', 'approved'):
                findings.append(f'glossary/terms.tsv:{n}: status must be proposed|approved, got {status!r}')
            if not th_term or not all(c.isascii() or '\u0e00' <= c <= '\u0e7f' for c in th_term):
                findings.append(f'glossary/terms.tsv:{n}: Thai term empty or has characters the fonts lack')
        print(f'glossary: {len(seen_terms)} term(s)')

    print(f'xml parser: {XML_PARSER}')
    print(f'examined: {len(items)} modinfo item(s), {len(text_files)} text file(s), '
          f'{checked} translated row(s), against {len(english)} tags ({en_files} catalogue units)')
    for f in findings:
        print('FINDING:', f)
    print(f'{len(findings)} finding(s)')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
