#!/usr/bin/env python3
"""Build the mod's fonts from the pristine OFL originals in fonts/src/.

Why the originals cannot ship as-is (measured 2026-11-06):
  * Neither Sarabun, Kanit nor any font the game ships has a glyph for U+200B ZERO WIDTH SPACE.
    Long Thai text needs U+200B to wrap (Gameface does not segment Thai: the 6a test line overflowed,
    6b with U+200B wrapped). With no glyph, each U+200B drew a visible gap in the letter-spaced main
    menu. (It was also blamed for the game's crash on quit; a control run with NO third-party mods (2026-11-06 08:28) crashed identically, so the crash is not ours.)
  * So: add an EMPTY, ZERO-ADVANCE glyph for U+200B (and its zero-width siblings), and rename the
    family (OFL good practice for a Modified Version; neither font declares a Reserved Font Name).

Requires fontTools:  pip install fonttools
"""
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), 'fonts')

# (source file, output file, new family name, style)
BUILDS = [
    ('Sarabun-Regular.ttf',  'lth-Sarabun-Regular.ttf',  'LTH Sarabun', 'Regular'),
    ('Sarabun-SemiBold.ttf', 'lth-Sarabun-SemiBold.ttf', 'LTH Sarabun', 'SemiBold'),
    ('Kanit-Medium.ttf',     'lth-Kanit-Medium.ttf',     'LTH Kanit',   'Medium'),
    ('Kanit-SemiBold.ttf',   'lth-Kanit-SemiBold.ttf',   'LTH Kanit',   'SemiBold'),
]
# ZERO WIDTH SPACE, ZW NON-JOINER, ZW JOINER, WORD JOINER, ZW NO-BREAK SPACE (BOM)
ZERO_WIDTH = [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF]


def build(src, dst, family, style):
    font = TTFont(os.path.join(FONTS, 'src', src))
    if 'glyf' not in font:
        raise SystemExit(f'{src}: not a TrueType-outline font; this script only handles glyf')
    cmap_best = font.getBestCmap()
    order = font.getGlyphOrder()
    added = []
    for cp in ZERO_WIDTH:
        if cp in cmap_best:
            continue
        name = f'uni{cp:04X}'
        if name not in order:
            order.append(name)
            font['glyf'].glyphs[name] = Glyph()  # empty outline
            font['hmtx'].metrics[name] = (0, 0)  # zero advance, zero lsb
        for table in font['cmap'].tables:
            if table.isUnicode():
                table.cmap[cp] = name
        added.append(f'U+{cp:04X}')
    font.setGlyphOrder(order)

    # The digital signature is invalid once the font is modified.
    if 'DSIG' in font:
        del font['DSIG']

    names = font['name']
    full = f'{family} {style}'
    ps = f'{family.replace(" ", "")}-{style}'
    for rec in list(names.names):
        if rec.nameID in (1, 16):
            names.setName(family, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
        elif rec.nameID == 4:
            names.setName(full, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
        elif rec.nameID == 6:
            names.setName(ps, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
        elif rec.nameID == 3:
            names.setName(f'{ps};LTH-Civ7', rec.nameID, rec.platformID, rec.platEncID, rec.langID)

    out = os.path.join(FONTS, dst)
    font.save(out)

    # Verify from the written file, not from memory.
    check = TTFont(out)
    cm = check.getBestCmap()
    for cp in ZERO_WIDTH:
        g = cm.get(cp)
        if g is None:
            raise SystemExit(f'{dst}: U+{cp:04X} not mapped after build')
        if check['hmtx'].metrics[g][0] != 0:
            raise SystemExit(f'{dst}: U+{cp:04X} has non-zero advance {check["hmtx"].metrics[g][0]}')
    thai = sum(1 for cp in range(0x0E01, 0x0E5C) if cp in cm)
    print(f'{dst}: added {added or "nothing (already present)"}, '
          f'{thai} Thai code points, family "{family}"')


def main():
    for b in BUILDS:
        build(*b)
    return 0


if __name__ == '__main__':
    sys.exit(main())
