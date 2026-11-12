#!/usr/bin/env python3
"""Draw the mod's 2D icons as transparent PNGs (original art; no Buddha images, by design).

  python3 tools/make_icons.py      (needs Pillow)

Writes icons/*.png at 256x256, drawn at 4x and downsampled for clean edges:
  civ_sym_lth_ayutthaya   white emblem: a prang rising over river waves (like the game's civ symbols)
  unitflag_lth_bang_rachan white: crossed Thai swords (daap song mue) - the villagers' weapon
  unitflag_lth_thammathut  white: a monk's alms bowl with its lid and stand
  buildicon_lth_ubosot     round gold-on-navy: tiered-roof ordination hall with chofa finials
  buildicon_lth_prang      round gold-on-navy: corncob prang on its stepped plinth
data/icons/icons.xml points the game at these through fs://game/lth-ayutthaya/icons/<name>.png
(the path form the official Database Modding doc gives for mod files).
"""
import math
import os

from PIL import Image, ImageDraw

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(MOD, 'icons')
S = 4                      # supersampling factor
N = 256                    # final size
WHITE = (255, 255, 255, 255)
GOLD = (222, 186, 112, 255)
NAVY = (22, 26, 40, 255)
RING = (150, 120, 70, 255)


def canvas():
    img = Image.new('RGBA', (N * S, N * S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img.resize((N, N), Image.LANCZOS).save(os.path.join(OUT, name + '.png'), optimize=True)
    print(f'wrote icons/{name}.png')


def p(x, y):
    """Coordinates in a 0..256 design space -> supersampled pixels."""
    return (x * S, y * S)


def prang_shape(d, cx, base, h, w, color):
    plinth = h * 0.24
    for i, f in enumerate((1.0, 0.84, 0.68)):
        y1 = base - plinth * i / 3
        y0 = y1 - plinth / 3 + 1
        d.rectangle([p(cx - w * f, y0), p(cx + w * f, y1)], fill=color)
    body_base, body_top = base - plinth, base - h * 0.86
    pts = []
    for k in range(61):
        t = k / 60
        y = body_base + (body_top - body_base) * t
        half = w * 0.6 * (1 - t ** 1.7) * (1 + 0.14 * math.sin(math.pi * t))
        notch = w * 0.05 if (k % 8 == 0 and 0 < k < 56) else 0
        pts.append(p(cx + max(half - notch, 1.2), y))
    pts += [(2 * cx * S - x, y) for x, y in reversed(pts)]
    d.polygon(pts, fill=color)
    d.line([p(cx, body_top), p(cx, base - h)], fill=color, width=int(w * 0.09 * S))


def waves(d, y, x0, x1, amp, color, width):
    for row in range(2):
        pts = [p(x, y + row * amp * 2.6 + amp * math.sin((x - x0) / (x1 - x0) * 4 * math.pi)) for x in range(int(x0), int(x1) + 1, 2)]
        d.line(pts, fill=color, width=int(width * S), joint='curve')


def civ_symbol():
    img, d = canvas()
    prang_shape(d, 128, 186, 168, 50, WHITE)
    waves(d, 204, 42, 214, 6, WHITE, 9)
    save(img, 'civ_sym_lth_ayutthaya')


def sword(d, angle, color):
    """A slightly curved Thai blade with a round guard and a long grip, rotated about the centre."""
    c, s = math.cos(angle), math.sin(angle)

    def rot(x, y):
        x, y = x - 128, y - 128
        return p(128 + x * c - y * s, 128 + x * s + y * c)

    blade = [(113, 44), (122, 26), (141, 46), (143, 148), (115, 148), (112, 70)]
    d.polygon([rot(x, y) for x, y in blade], fill=color)
    d.polygon([rot(x, y) for x, y in ((102, 148), (156, 148), (150, 160), (108, 160))], fill=color)  # guard
    d.polygon([rot(x, y) for x, y in ((121, 160), (137, 160), (138, 214), (120, 214))], fill=color)  # grip
    gx, gy = rot(128, 222)
    r = 9 * S
    d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=color)  # pommel


def bang_rachan():
    img, d = canvas()
    sword(d, math.radians(-32), WHITE)
    sword(d, math.radians(32), WHITE)
    save(img, 'unitflag_lth_bang_rachan')


def thammathut():
    img, d = canvas()
    d.chord([p(52, 92), p(204, 214)], 0, 180, fill=WHITE)                    # bowl
    d.rectangle([p(52, 150), p(204, 153)], fill=WHITE)
    d.chord([p(70, 96), p(186, 150)], 180, 360, fill=WHITE)                  # lid
    d.ellipse([p(118, 82), p(138, 102)], fill=WHITE)                         # lid knob
    d.polygon([p(92, 214), p(164, 214), p(178, 232), p(78, 232)], fill=WHITE)  # stand
    save(img, 'unitflag_lth_thammathut')


def round_base(d):
    d.ellipse([p(6, 6), p(250, 250)], fill=RING)
    d.ellipse([p(14, 14), p(242, 242)], fill=NAVY)


def ubosot_icon():
    img, d = canvas()
    round_base(d)
    x0, w, base = 58, 140, 196
    d.rectangle([p(x0 + 10, base - 46), p(x0 + w - 10, base)], fill=GOLD)
    for i in range(5):  # columns read as dark gaps
        cx = x0 + 22 + i * (w - 44) / 4
        d.rectangle([p(cx - 4, base - 40), p(cx + 4, base)], fill=NAVY)
    for i, f in enumerate((1.0, 0.76, 0.52)):
        inset = w * (1 - f) / 2
        y = base - 46 - i * 20
        left, right = x0 + inset - 8, x0 + w - inset + 8
        d.polygon([p(left, y), p(right, y), p(x0 + w / 2, y - 52)], fill=GOLD)
        for sx, dx in ((left, 9), (right, -9)):
            d.line([p(sx, y), p(sx + dx, y - 20)], fill=GOLD, width=5 * S)
    d.line([p(x0 + w / 2, base - 46 - 40 - 52), p(x0 + w / 2, base - 46 - 40 - 76)], fill=GOLD, width=5 * S)
    d.rectangle([p(x0 - 4, base), p(x0 + w + 4, base + 8)], fill=GOLD)
    save(img, 'buildicon_lth_ubosot')


def prang_icon():
    img, d = canvas()
    round_base(d)
    prang_shape(d, 128, 204, 168, 46, GOLD)
    save(img, 'buildicon_lth_prang')


if __name__ == '__main__':
    civ_symbol()
    bang_rachan()
    thammathut()
    ubosot_icon()
    prang_icon()
