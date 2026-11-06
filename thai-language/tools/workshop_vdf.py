#!/usr/bin/env python3
"""Write dist/workshop_item.vdf for `steamcmd +workshop_build_item`.

Paths in a VDF must be absolute, so it is generated per machine into dist/ (not committed).
Run tools/package.sh first: the content folder is the gated build in dist/lth-thai-language.

  tools/workshop_vdf.py [--private] [--no-preview] ["change note"]

--no-preview: steamcmd uploads the preview through legacy Steam Cloud, which Civ VII refuses
("Access Denied" after content uploaded fine, 2026-11-06); this sends everything else.

First upload: workshop/published_id.txt is absent -> publishedfileid 0 creates a NEW item, uploaded
PRIVATE (visibility 2). steamcmd then prints the new id: save it in workshop/published_id.txt so every
later run updates that item instead of creating another. Visibility of an existing item is left as set
on its Steam page.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
APP_ID = '1295660'  # Sid Meier's Civilization VII
TITLE = 'Thai Language Pack - ภาษาไทย'


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    content = os.path.join(MOD, 'dist', 'lth-thai-language')
    if not os.path.isfile(os.path.join(content, 'thai-language.modinfo')):
        print('COULD NOT LOOK: no build in dist/lth-thai-language — run tools/package.sh first')
        return 2
    # steamcmd's VDF reader ends a value at the first double quote even when escaped: the first
    # description was cut at 'แล้วเปิดใช้ \' (2026-11-06). Refuse instead of publishing a truncated page.
    for name in ('description.txt',):
        text = open(os.path.join(MOD, 'workshop', name), encoding='utf-8').read()
        if '"' in text or '\\' in text:
            print(f'workshop/{name}: contains a double quote or backslash, which steamcmd truncates at')
            return 1
    modinfo = open(os.path.join(MOD, 'thai-language.modinfo'), encoding='utf-8').read()
    ver = re.search(r'<Mod id="lth-thai-language" version="(\d+)"', modinfo).group(1)
    id_path = os.path.join(MOD, 'workshop', 'published_id.txt')
    pid = open(id_path).read().strip() if os.path.isfile(id_path) else '0'
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    note = args[0] if args else f'Version {ver}'
    fields = [
        ('appid', APP_ID),
        ('publishedfileid', pid),
        ('contentfolder', content),
        ('previewfile', os.path.join(MOD, 'workshop', 'preview.png')),
        ('title', TITLE),
        ('description', open(os.path.join(MOD, 'workshop', 'description.txt'), encoding='utf-8').read().strip()),
        ('changenote', note),
    ]
    if '--no-preview' in sys.argv:
        fields = [f for f in fields if f[0] != 'previewfile']
    if pid == '0' or '--private' in sys.argv:
        fields.append(('visibility', '2'))  # private until tested from the Workshop copy
    out = os.path.join(MOD, 'dist', 'workshop_item.vdf')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('"workshopitem"\n{\n' + ''.join(f'\t{q(k)}\t\t{q(v)}\n' for k, v in fields) + '}\n')
    print(f'{out}: {"NEW private item" if pid == "0" else "update of item " + pid}, version {ver}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
