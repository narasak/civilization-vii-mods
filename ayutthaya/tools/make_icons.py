#!/usr/bin/env python3
"""Draw the mod's 2D icons as transparent PNGs (original art; no Buddha images, by design).

  python3 tools/make_icons.py      (needs Pillow)

Writes icons/*.png at 256x256, drawn at 8x and downsampled for clean edges. Redrawn 2026-11-16
(docs/superpowers/specs/2026-11-16-ayutthaya-icon-redraw-design.md): curves instead of basic shapes,
and every icon must still read at 32 px.
  civ_sym_lth_ayutthaya    white emblem: a prang with two satellite prangs over river waves
  unitflag_lth_bang_rachan white: crossed Thai daap with guard, wrapped grip and pommel
  unitflag_lth_thammathut  white: a monk's alms bowl with lid, knob and stand
  unitflag_lth_chang_song  white: a royal war elephant with howdah and tiered parasol
  buildicon_lth_ubosot     painted medallion: tiered terracotta roof, gold trim and chofa, cream walls
  buildicon_lth_prang      painted medallion: shaded gold corncob prang with satellite prangs
Unit flags and the civ symbol stay single-colour white, like the game's own; the building icons are
shaded, like the game's building icons. data/icons/icons.xml points the game at these through
fs://game/lth-ayutthaya/icons/<name>.png.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(MOD, 'icons')
S = 8                      # supersampling factor
N = 256                    # final size
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


# ------------------------------------------------------------------ geometry helpers (design space 0..256)
def p(x, y):
    return (x * S, y * S)


def cubic(a, b, c, d, n=28):
    out = []
    for k in range(1, n + 1):
        t = k / n
        u = 1 - t
        out.append((u ** 3 * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t ** 3 * d[0],
                    u ** 3 * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t ** 3 * d[1]))
    return out


def path(start, *segs):
    """Polygon from a start point and segments: (x, y) for a line, or ((c1), (c2), (end)) for a curve."""
    pts, cur = [start], start
    for s in segs:
        if isinstance(s[0], tuple):
            pts += cubic(cur, s[0], s[1], s[2])
            cur = s[2]
        else:
            pts.append(s)
            cur = s
    return [p(x, y) for x, y in pts]


def mirror(half, cx=128):
    """Close a left-to-centre outline (top to bottom) into a symmetric polygon about x = cx."""
    return half + [(2 * cx * S - x, y) for x, y in reversed(half)]


def rot(pts, angle, cx=128, cy=128):
    ca, sa = math.cos(angle), math.sin(angle)
    return [p(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def canvas():
    img = Image.new('RGBA', (N * S, N * S), CLEAR)
    return img, ImageDraw.Draw(img)


def mask():
    m = Image.new('L', (N * S, N * S), 0)
    return m, ImageDraw.Draw(m)


def vgrad(top, bottom, y0=0, y1=N):
    """Full-canvas vertical gradient between two RGB colours, from design y0 to y1."""
    g = Image.new('RGBA', (1, N * S))
    for y in range(N * S):
        t = min(max((y / S - y0) / (y1 - y0), 0), 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    return g.resize((N * S, N * S))


def paint(img, m, fill):
    """Composite a colour or a gradient image onto img through mask m."""
    src = Image.new('RGBA', img.size, fill) if isinstance(fill, tuple) else fill
    img.paste(src, (0, 0), m)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img.resize((N, N), Image.LANCZOS).save(os.path.join(OUT, name + '.png'), optimize=True)
    print(f'wrote icons/{name}.png')


# ------------------------------------------------------------------ shared shapes
def prang_outline(cx, base, h, w):
    """Corncob prang: stepped redented plinth, swelling banded body, finial. Returns (body, bands, finial)."""
    plinth = h * 0.22
    body_base, body_top = base - plinth, base - h * 0.84
    polys = []
    for i, f in enumerate((1.0, 0.86, 0.72)):          # three redented plinth steps
        y1 = base - plinth * i / 3
        y0 = y1 - plinth / 3
        hw = w * f
        polys.append([p(cx - hw, y1), p(cx - hw, y0 + 2), p(cx - hw + 3, y0 + 2), p(cx - hw + 3, y0),
                      p(cx + hw - 3, y0), p(cx + hw - 3, y0 + 2), p(cx + hw, y0 + 2), p(cx + hw, y1)])
    half = []
    for k in range(80):
        t = k / 79
        y = body_base + (body_top - body_base) * t
        r = w * 0.56 * (1 - t ** 2.3) * (1 + 0.34 * math.sin(math.pi * t * 0.85)) + 0.8
        half.append(p(cx - r, y))
    body = mirror(half, cx)
    bands = []
    for t in (0.12, 0.27, 0.41, 0.54, 0.66, 0.77):     # horizontal tier lines of the corncob
        y = body_base + (body_top - body_base) * t
        r = w * 0.56 * (1 - t ** 2.3) * (1 + 0.34 * math.sin(math.pi * t * 0.85))
        bands.append((p(cx - r, y), p(cx + r, y)))
    tip = base - h
    finial = [p(cx - 1.6, body_top), p(cx - 1.6, tip + 10), p(cx - 6, tip + 14), p(cx - 6.5, tip + 8),
              p(cx - 2, tip + 9), p(cx, tip), p(cx + 2, tip + 9), p(cx + 6.5, tip + 8), p(cx + 6, tip + 14),
              p(cx + 1.6, tip + 10), p(cx + 1.6, body_top)]
    return polys + [body], bands, finial


def draw_prang(d, cx, base, h, w, fill, line):
    polys, bands, finial = prang_outline(cx, base, h, w)
    for poly in polys + [finial]:
        d.polygon(poly, fill=fill)
    for a, b in bands:
        d.line([a, b], fill=line, width=int(max(w * 0.07, 1.6) * S))


def wave_rows(d, x0, x1, y, rows, amp, gap, width, color):
    for r in range(rows):
        inset = r * 10
        pts = [p(x, y + r * gap + amp * math.sin((x - x0) / 34 * 2 * math.pi))
               for x in range(int(x0 + inset), int(x1 - inset) + 1)]
        d.line(pts, fill=color, width=int(width * S), joint='curve')


# ------------------------------------------------------------------ white emblems (civ symbol, unit flags)
def civ_symbol():
    img, d = canvas()
    draw_prang(d, 80, 184, 96, 24, WHITE, CLEAR)
    draw_prang(d, 176, 184, 96, 24, WHITE, CLEAR)
    m, md = mask()                                     # clear a margin round the main prang so it stands out
    polys, _, finial = prang_outline(128, 188, 172, 48)
    for poly in polys + [finial]:
        md.polygon(poly, fill=255)
    m = m.filter(ImageFilter.MaxFilter(8 * 3 + 1))
    paint(img, m, CLEAR)
    draw_prang(d, 128, 188, 172, 48, WHITE, CLEAR)
    wave_rows(d, 36, 220, 202, 3, 4.5, 11, 6.5, WHITE)
    save(img, 'civ_sym_lth_ayutthaya')


def daap(angle):
    """One Thai sword (daap) in local coordinates along +y, rotated about the centre."""
    blade = path((-6, -96), ((-9, -60), (-10, -20), (-8, 18)), (8, 18), ((9, -16), (11, -58), (12, -88)),
                 ((10, -100), (4, -108), (-6, -96)))
    guard = path((-18, 18), (18, 18), ((20, 21), (20, 25), (18, 26)), (-18, 26), ((-20, 25), (-20, 21), (-18, 18)))
    grip = path((-5.5, 26), (5.5, 26), (6, 78), (-6, 78))
    pommel = [(7.5 * math.cos(a / 20 * 2 * math.pi), 84 + 7.5 * math.sin(a / 20 * 2 * math.pi)) for a in range(20)]
    lift = lambda poly: [((x / S) - 0, (y / S)) for x, y in poly]
    return [rot(lift(blade), angle), rot(lift(guard), angle), rot(lift(grip), angle), rot(pommel, angle)], \
        [rot([(-7, y), (7, y)], angle) for y in (38, 50, 62)], rot([(0, -86), (0, 10)], angle)


def bang_rachan():
    img, d = canvas()
    for i, angle in enumerate((math.radians(34), math.radians(-34))):
        parts, wraps, fuller = daap(angle)
        if i == 1:                                     # clear a margin so the front sword crosses cleanly
            m, md = mask()
            for poly in parts:
                md.polygon(poly, fill=255)
            paint(img, m.filter(ImageFilter.MaxFilter(8 * 3 + 1)), CLEAR)
        for poly in parts:
            d.polygon(poly, fill=WHITE)
        for w in wraps:                                # grip wrapping
            d.line(w, fill=CLEAR, width=int(2.2 * S))
        d.line(fuller, fill=CLEAR, width=int(1.6 * S))  # blade fuller line
    save(img, 'unitflag_lth_bang_rachan')


def thammathut():
    img, d = canvas()
    bowl = path((52, 132), (204, 132), ((204, 186), (172, 214), (128, 214)), ((84, 214), (52, 186), (52, 132)))
    d.polygon(bowl, fill=WHITE)
    d.polygon(path((70, 132), ((74, 98), (100, 84), (128, 84)), ((156, 84), (182, 98), (186, 132))), fill=WHITE)  # lid
    d.polygon(path((116, 84), ((114, 74), (120, 66), (128, 66)), ((136, 66), (142, 74), (140, 84))), fill=WHITE)  # knob
    d.polygon(path((96, 216), (160, 216), (172, 234), (84, 234)), fill=WHITE)                                     # stand
    for a, b in (((48, 132), (208, 132)), ((90, 214), (166, 214))):                                              # seams
        d.line([p(*a), p(*b)], fill=CLEAR, width=int(3 * S))
    d.line(path((60, 146), (196, 146)), fill=CLEAR, width=int(2.4 * S))                                           # rim band
    d.line(path((84, 112), ((100, 100), (114, 96), (128, 96)))[1:], fill=CLEAR, width=int(2.2 * S))               # lid highlight
    save(img, 'unitflag_lth_thammathut')


def chang_song():
    img, d = canvas()
    body = path((104, 86),
                ((130, 70), (170, 70), (192, 90)),             # back
                ((206, 104), (210, 132), (204, 162)),          # rump
                (200, 214), (180, 214), (178, 176),            # hind leg
                ((160, 184), (130, 184), (112, 176)),          # belly
                (110, 214), (90, 214), (88, 164),              # front leg
                ((84, 150), (74, 142), (66, 138)),             # chest to mouth
                ((58, 162), (58, 186), (62, 198)),             # trunk down (inner edge)
                ((64, 210), (52, 218), (42, 210)),             # trunk tip curls forward
                ((38, 204), (42, 198), (47, 201)),
                ((40, 182), (38, 150), (44, 124)),             # trunk outer edge going up
                ((46, 96), (62, 70), (84, 68)),                # forehead
                ((94, 68), (100, 76), (104, 86)))
    d.polygon(body, fill=WHITE)
    for x in (98, 188):                                        # far legs, slightly behind
        d.polygon(path((x - 8, 176), (x + 8, 176), (x + 7, 208), (x - 7, 208)), fill=WHITE)
    d.polygon(path((64, 140), ((50, 150), (34, 150), (26, 140)), ((36, 146), (50, 142), (62, 134))), fill=WHITE)  # tusk
    d.line(path((26, 141), ((36, 147), (50, 144), (62, 136)))[1:], fill=CLEAR, width=int(1.6 * S))
    d.line(path((92, 92), ((112, 96), (118, 120), (104, 138)), ((96, 144), (88, 140), (86, 132)))[1:],
           fill=CLEAR, width=int(2.4 * S))                     # ear
    d.ellipse([p(66, 96), p(73, 103)], fill=CLEAR)             # eye
    d.line(path((204, 120), ((218, 132), (220, 152), (214, 168)))[1:], fill=WHITE, width=int(3 * S))  # tail
    d.ellipse([p(209, 164), p(219, 180)], fill=WHITE)                                 # tail tuft
    d.polygon(path((116, 76), (168, 76), (172, 94), (112, 94)), fill=WHITE)            # saddle cloth
    d.line([p(110, 96), p(174, 96)], fill=CLEAR, width=int(2.4 * S))
    d.polygon(path((122, 74), (124, 52), (160, 52), (162, 74)), fill=WHITE)            # howdah
    d.line([p(118, 76), p(166, 76)], fill=CLEAR, width=int(2.4 * S))
    d.line([p(142, 52), p(142, 16)], fill=WHITE, width=int(2.6 * S))                   # parasol pole
    for y, hw in ((40, 22), (30, 17), (21, 12)):                                       # three-tier parasol
        d.polygon(path((142 - hw, y), ((142 - hw * 0.6, y - 7), (142 + hw * 0.6, y - 7), (142 + hw, y))), fill=WHITE)
    d.polygon(path((140, 14), (142, 6), (144, 14)), fill=WHITE)
    save(img, 'unitflag_lth_chang_song')


# ------------------------------------------------------------------ painted medallions (building icons)
NAVY_TOP, NAVY_BOT = (34, 44, 74), (12, 15, 28)
GOLD_LIGHT, GOLD_DARK, GOLD_LINE = (248, 222, 150), (176, 128, 52), (110, 76, 30)


def medallion():
    img, _ = canvas()
    m, md = mask()
    md.ellipse([p(6, 6), p(250, 250)], fill=255)
    paint(img, m, vgrad(GOLD_LIGHT, GOLD_DARK, 6, 250))                 # gold rim
    m, md = mask()
    md.ellipse([p(15, 15), p(241, 241)], fill=255)
    paint(img, m, (90, 64, 26, 255))                                    # rim inner edge
    m, md = mask()
    md.ellipse([p(18, 18), p(238, 238)], fill=255)
    paint(img, m, vgrad(NAVY_TOP, NAVY_BOT, 18, 238))                   # navy field
    glow, gd = mask()
    gd.ellipse([p(52, 40), p(204, 196)], fill=70)
    img.paste(Image.new('RGBA', img.size, (120, 150, 210, 255)), (0, 0), ImageChops.multiply(glow.filter(ImageFilter.GaussianBlur(40 * S / 4)), m))
    return img


def shadow(img, m, off=4, blur=5):
    sh = Image.new('L', img.size, 0)
    sh.paste(m.filter(ImageFilter.GaussianBlur(blur * S)), (off * S, off * S))
    img.paste(Image.new('RGBA', img.size, (0, 0, 0, 255)), (0, 0), sh.point(lambda v: v * 0.55))


def ubosot_icon():
    img = medallion()
    roof_lo = path((44, 146), ((60, 138), (70, 124), (78, 116)), (178, 116), ((186, 124), (196, 138), (212, 146)), (196, 150), (60, 150))
    roof_mid = path((60, 120), ((72, 112), (80, 102), (88, 96)), (168, 96), ((176, 102), (184, 112), (196, 120)), (60, 120))
    gable = path((84, 100), (128, 50), (172, 100))
    walls = path((70, 150), (186, 150), (186, 194), (70, 194))
    base1 = path((60, 194), (196, 194), (196, 202), (60, 202))
    base2 = path((50, 202), (206, 202), (206, 212), (50, 212))
    whole, wd = mask()
    for poly in (roof_lo, roof_mid, gable, walls, base1, base2):
        wd.polygon(poly, fill=255)
    shadow(img, whole)
    d = ImageDraw.Draw(img)
    m, md = mask()
    md.polygon(walls, fill=255)
    paint(img, m, vgrad((250, 240, 216), (206, 190, 158), 150, 194))
    for x in (82, 104, 152, 174):                                        # columns
        d.rectangle([p(x - 4, 152), p(x + 4, 194)], fill=(214, 176, 92, 255))
    d.polygon(path((116, 194), (116, 166), ((116, 158), (140, 158), (140, 166)), (140, 194)), fill=(96, 50, 30, 255))  # door
    for poly, top, bot in ((roof_lo, (214, 96, 62), (130, 44, 30)), (roof_mid, (222, 108, 70), (140, 50, 34)),
                           (gable, (232, 122, 78), (150, 56, 38))):
        m, md = mask()
        md.polygon(poly, fill=255)
        paint(img, m, vgrad(top, bot, 50, 150))
    for a, b in (((44, 146), (78, 116)), ((212, 146), (178, 116)), ((60, 120), (88, 96)), ((196, 120), (168, 96)),
                 ((84, 100), (128, 50)), ((172, 100), (128, 50))):       # gold barge boards
        d.line([p(*a), p(*b)], fill=GOLD_LIGHT + (255,), width=int(4 * S))
    d.polygon(path((112, 96), (128, 66), (144, 96)), fill=(236, 196, 104, 255))   # gable ornament
    for x, y, s in ((44, 146, -1), (212, 146, 1), (60, 120, -1), (196, 120, 1), (128, 50, 0)):   # chofa finials
        if s == 0:
            d.polygon(path((126, 52), ((124, 40), (130, 32), (136, 30)), ((132, 36), (130, 44), (130, 52))), fill=GOLD_LIGHT + (255,))
        else:
            d.polygon(path((x, y), ((x + s * 8, y - 8), (x + s * 8, y - 18), (x + s * 2, y - 22)),
                           ((x + s * 6, y - 14), (x + s * 3, y - 8), (x - s * 3, y - 2))), fill=GOLD_LIGHT + (255,))
    for poly in (base1, base2):
        m, md = mask()
        md.polygon(poly, fill=255)
        paint(img, m, vgrad((236, 226, 204), (170, 156, 132), 194, 212))
    save(img, 'buildicon_lth_ubosot')


def prang_icon():
    img = medallion()
    whole, wd = mask()
    for cx, base, h, w in ((78, 200, 92, 22), (178, 200, 92, 22), (128, 206, 176, 44)):
        polys, _, finial = prang_outline(cx, base, h, w)
        for poly in polys + [finial]:
            wd.polygon(poly, fill=255)
    shadow(img, whole)
    for cx, base, h, w, dim in ((78, 200, 92, 22, 0.78), (178, 200, 92, 22, 0.78), (128, 206, 176, 44, 1.0)):
        polys, bands, finial = prang_outline(cx, base, h, w)
        m, md = mask()
        for poly in polys + [finial]:
            md.polygon(poly, fill=255)
        top = tuple(int(c * dim) for c in GOLD_LIGHT)
        bot = tuple(int(c * dim) for c in GOLD_DARK)
        paint(img, m, vgrad(top, bot, base - h, base))
        side, sd = mask()                                                # shaded right flank
        sd.rectangle([p(cx + w * 0.12, base - h), p(cx + w, base)], fill=110)
        img.paste(Image.new('RGBA', img.size, (90, 56, 18, 255)), (0, 0), ImageChops.multiply(side, m))
        d = ImageDraw.Draw(img)
        for a, b in bands:
            d.line([a, b], fill=GOLD_LINE + (255,), width=int(max(w * 0.06, 1.4) * S))
    d = ImageDraw.Draw(img)
    d.polygon(path((120, 176), (120, 162), ((120, 152), (136, 152), (136, 162)), (136, 176)), fill=(60, 38, 18, 255))  # niche
    save(img, 'buildicon_lth_prang')


if __name__ == '__main__':
    civ_symbol()
    bang_rachan()
    thammathut()
    chang_song()
    ubosot_icon()
    prang_icon()
