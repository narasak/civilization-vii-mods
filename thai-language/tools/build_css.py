#!/usr/bin/env python3
"""Ship the Thai fonts in a stylesheet the game loads BEFORE any mod script runs.

Why: mod UIScripts start about 4 s after the loading screen appears (UI.log "LTH: build" at 13:25:59,
loading-screen screenshot at 13:25:55 on 2026-11-06), so Thai on the loading screen rendered as boxes.
core/ui/themes/default/panel-animations.css is <link>ed by both root-shell.html and root-game.html, so a
copy of it with our font rules appended would give Thai a font from the first frame.

Whether a mod's ImportFiles can replace a game file is NOT documented. Two candidate paths are shipped,
each setting a different marker, and lth-thai-fonts.js logs which one won ("LTH: early-css"):
    ui/themes/default/panel-animations.css        -> --lth-early-css: 1
    core/ui/themes/default/panel-animations.css   -> --lth-early-css: 2
The copies are ORIGINAL BYTES + our block. tools/check.py fails when the game's file changes, so a stale
copy can never silently replace a newer original.

Single source: the selector lists and stacks are read from ui/lth-thai-fonts.js.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
GAME = os.environ.get(
    'CIV7_RESOURCES',
    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/"
                       "Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources"))
ORIGINAL = os.path.join(GAME, 'Base', 'modules', 'core', 'ui', 'themes', 'default', 'panel-animations.css')
# Measured 2026-11-06: only the module-qualified path replaces the game's file (UI.log "LTH: early-css 2",
# in both shell and game). The bare ui/... path (marker 1) never took effect and is no longer shipped.
TARGETS = {'core/ui/themes/default/panel-animations.css': 2}
MARK = '/* LTH-THAI-FONTS: appended by tools/build_css.py */'


def js_list(js, name):
    m = re.search(r'const ' + name + r' = \[(.*?)\];', js, re.S)
    if not m:
        raise SystemExit(f'COULD NOT LOOK: {name} not found in ui/lth-thai-fonts.js')
    body = re.sub(r'//[^\n]*', '', m.group(1))  # comments hold apostrophes ("game's") that pair wrongly
    items = re.findall(r"'([^'\n]+)'", body)
    bad = [x for x in items if not re.fullmatch(r'[A-Za-z0-9_.\- ]+', x)]
    if bad or not items:
        raise SystemExit(f'COULD NOT LOOK: {name} parsed to implausible selectors {bad or items}')
    return items


def js_const(js, name):
    m = re.search(r"const " + name + r" = '([^']+)';", js)
    if not m:
        raise SystemExit(f'COULD NOT LOOK: {name} not found in ui/lth-thai-fonts.js')
    return m.group(1)


def faces(family, regular, bold, src):
    """One @font-face per CSS weight 100-900. With only 400/700 declared, the loading screen's
    font-medium (500) title found no face ("LTH-Kanit ... Medium (500) hasn't been loaded")."""
    return [f'@font-face {{ font-family: "{family}"; src: {src(regular if w <= 500 else bold)}; font-weight: {w}; }}'
            for w in range(100, 1000, 100)]


def block(js, marker):
    body, title = js_const(js, 'FAMILY_BODY'), js_const(js, 'FAMILY_TITLE')
    mod_id = js_const(js, 'MOD_ID')
    sizes = js_list(js, 'SIZES')
    sb, st = js_list(js, 'STATIC_BODY'), js_list(js, 'STATIC_TITLE')

    def src(f):
        return f'url("fs://game/{mod_id}/fonts/{f}"), url("fs://game/fonts/{f}")'
    sbody = f'BodyFont, "{body}", "BodyFont-SC", "BodyFont-TC", "BodyFont-JP", "BodyFont-KR"'
    stitle = f'TitleFont, "{title}", "TitleFont-SC", "TitleFont-TC", "TitleFont-JP", "TitleFont-KR"'
    t_sel = ['.font-title'] + [f'.font-title-{z}' for z in sizes] + st
    b_sel = ['.font-body'] + [f'.font-body-{z}' for z in sizes] + sb
    j = lambda xs: ',\n'.join(f'html {x}' for x in xs)
    return '\n'.join([
        '', MARK,
        *faces(body, 'lth-Sarabun-Regular.ttf', 'lth-Sarabun-SemiBold.ttf', src),
        *faces(title, 'lth-Kanit-Medium.ttf', 'lth-Kanit-SemiBold.ttf', src),
        f'{j(t_sel)} {{ font-family: {stitle}; }}',
        f'{j(b_sel)} {{ font-family: {sbody}; }}',
        f'html, body {{ font-family: {sbody}; }}',
        js_const(js, 'THAI_LEADING'),  # the loading screen shows before any mod script runs
        f'html {{ --lth-early-css: {marker}; }}',
        '',
    ])


def main():
    if not os.path.isfile(ORIGINAL):
        print(f'COULD NOT LOOK: {ORIGINAL}')
        return 2
    original = open(ORIGINAL, 'rb').read()
    js = open(os.path.join(MOD, 'ui', 'lth-thai-fonts.js'), encoding='utf-8').read()
    for rel, marker in TARGETS.items():
        out = os.path.join(MOD, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as f:
            f.write(original + block(js, marker).encode('utf-8'))
        print(f'{rel}: {len(original)} original bytes + font block (marker {marker})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
