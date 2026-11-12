#!/usr/bin/env python3
"""Draw the civilization panel art: Ayutthaya's skyline at dusk across the river.

  python3 tools/make_panel.py      (needs Pillow)

The setup screen and the narrative panel look up an image named bg-panel-<civ> (core civ-select-model.js:
`bg-panel-${civID.replace("CIVILIZATION_", "").toLowerCase()}`), so this writes art/bg-panel-lth_ayutthaya.png.
Original art drawn here, so the mod ships nothing of the game's.
Silhouettes: Wat Chaiwatthanaram's five prangs (centre), Wat Phra Si Sanphet's three bell chedis (left),
a tiered-roof ubosot (right), sugar palms, a long boat on the Chao Phraya.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
HORIZON = 720
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(MOD, 'art', 'bg-panel-lth_ayutthaya.png')
OUT_VERT = os.path.join(MOD, 'art', 'lth_ayutthaya_vert.png')


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(img):
    top, mid, low = (22, 20, 52), (120, 62, 88), (240, 150, 70)
    px = img.load()
    for y in range(HORIZON):
        t = y / HORIZON
        c = lerp(top, mid, t / 0.6) if t < 0.6 else lerp(mid, low, (t - 0.6) / 0.4)
        for x in range(W):
            px[x, y] = c


def sun(img):
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    cx, cy = 1180, HORIZON - 120
    for r, a in ((260, 40), (170, 70), (95, 140)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 196, 110, a))
    d.ellipse((cx - 60, cy - 60, cx + 60, cy + 60), fill=(255, 226, 160, 255))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))


def prang(d, cx, base, h, w, color):
    """Corncob tower: stepped plinth, a body that swells then narrows to a rounded tip, a finial."""
    plinth = h * 0.22
    for i, f in enumerate((1.0, 0.86, 0.72)):
        y0 = base - plinth * i / 3
        d.rectangle((cx - w * f, y0 - plinth / 3, cx + w * f, y0), fill=color)
    body_base, body_top = base - plinth, base - h * 0.88
    pts = []
    for k in range(41):
        t = k / 40
        y = body_base + (body_top - body_base) * t
        half = w * 0.58 * (1 - t ** 1.8) * (1 + 0.12 * math.sin(math.pi * t))
        half -= (k % 5 == 0) * w * 0.04  # tier notches
        pts.append((cx + max(half, 2), y))
    pts += [(2 * cx - x, y) for x, y in reversed(pts)]
    d.polygon(pts, fill=color)
    d.line((cx, body_top, cx, base - h), fill=color, width=max(3, int(w * 0.06)))


def chedi(d, cx, base, h, w, color):
    """Sri Lankan-style bell chedi: tiered base, bell, square harmika, tapering rings to a spire."""
    d.rectangle((cx - w, base - h * 0.12, cx + w, base), fill=color)
    d.rectangle((cx - w * 0.8, base - h * 0.2, cx + w * 0.8, base - h * 0.12), fill=color)
    bell_bottom, bell_top = base - h * 0.2, base - h * 0.55
    pts = []
    for k in range(31):
        t = k / 30
        y = bell_bottom + (bell_top - bell_bottom) * t
        pts.append((cx + w * 0.72 * math.cos(t * math.pi / 2) ** 0.7 + 1, y))
    pts += [(2 * cx - x, y) for x, y in reversed(pts)]
    d.polygon(pts, fill=color)
    d.rectangle((cx - w * 0.22, bell_top - h * 0.06, cx + w * 0.22, bell_top), fill=color)
    d.polygon([(cx - w * 0.16, bell_top - h * 0.06), (cx + w * 0.16, bell_top - h * 0.06), (cx, base - h)], fill=color)


def ubosot(d, x0, base, w, h, color):
    """Hall with three stacked gables and chofa finials."""
    d.rectangle((x0, base - h * 0.35, x0 + w, base), fill=color)
    for i, f in enumerate((1.0, 0.78, 0.56)):
        inset = w * (1 - f) / 2
        y = base - h * 0.35 - i * h * 0.17
        apex = y - h * 0.38
        d.polygon([(x0 + inset - w * 0.04, y), (x0 + w - inset + w * 0.04, y), (x0 + w / 2, apex)], fill=color)
        for sx in (x0 + inset - w * 0.04, x0 + w - inset + w * 0.04):
            d.line((sx, y, sx + (8 if sx < x0 + w / 2 else -8), y - 22), fill=color, width=4)
        d.line((x0 + w / 2, apex, x0 + w / 2, apex - 26), fill=color, width=4)


def palm(d, x, base, h, color):
    lean = random.uniform(-12, 12)
    d.line((x, base, x + lean, base - h), fill=color, width=6)
    top = (x + lean, base - h)
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.line((top, (top[0] + math.cos(r) * 46, top[1] + math.sin(r) * 22 + 10)), fill=color, width=5)


def skyline(d, color):
    random.seed(1767)
    d.rectangle((0, HORIZON - 26, W, HORIZON), fill=color)  # river bank and walls
    for x in range(40, W, 140):
        palm(d, x + random.randint(-30, 30), HORIZON - 20, random.randint(90, 150), color)
    for cx, h in ((260, 330), (380, 360), (500, 330)):
        chedi(d, cx, HORIZON - 20, h, 60, color)
    prang(d, 980, HORIZON - 20, 470, 120, color)
    for dx, h in ((-190, 280), (190, 280), (-330, 200), (330, 200)):
        prang(d, 980 + dx, HORIZON - 20, h, 70, color)
    ubosot(d, 1460, HORIZON - 20, 300, 260, color)
    ubosot(d, 1760, HORIZON - 20, 180, 170, color)


def water(img):
    px = img.load()
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        for x in range(W):
            px[x, y] = lerp((70, 40, 60), (14, 14, 34), t)
    refl = img.crop((0, HORIZON - (H - HORIZON), W, HORIZON)).transpose(Image.FLIP_TOP_BOTTOM)
    refl = refl.filter(ImageFilter.GaussianBlur(3))
    mask = Image.linear_gradient('L').resize((W, H - HORIZON)).point(lambda v: int(150 - v * 0.55))
    img.paste(refl, (0, HORIZON), mask)
    d = ImageDraw.Draw(img)
    random.seed(1351)
    for _ in range(260):
        y = random.randint(HORIZON + 6, H)
        x = random.randint(0, W)
        d.line((x, y, x + random.randint(20, 90), y), fill=(255, 190, 120, 70), width=1)


def boat(d, color):
    x, y = 520, 900
    d.polygon([(x - 260, y - 30), (x + 260, y - 30), (x + 230, y), (x - 230, y)], fill=color)
    d.line((x + 255, y - 30, x + 300, y - 95), fill=color, width=10)  # raised prow
    for i in range(14):
        rx = x - 200 + i * 30
        d.ellipse((rx - 7, y - 58, rx + 7, y - 44), fill=color)
        d.line((rx, y - 44, rx, y - 30), fill=color, width=6)
        d.line((rx + 4, y - 40, rx + 22, y + 18), fill=color, width=3)


def main():
    img = Image.new('RGBA', (W, H))
    sky(img)
    sun(img)
    d = ImageDraw.Draw(img)
    skyline(d, (18, 12, 26, 255))
    water(img)
    boat(ImageDraw.Draw(img), (10, 8, 18, 255))
    vignette = Image.radial_gradient('L').resize((W, H)).point(lambda v: int(v * 0.6))
    img = Image.composite(Image.new('RGBA', (W, H), (0, 0, 0, 255)), img, vignette)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img = img.convert('RGB')
    img.save(OUT, optimize=True)
    print(f'wrote {os.path.relpath(OUT, MOD)} ({W}x{H}, {os.path.getsize(OUT) // 1024} KB)')
    # Portrait crop around the central prang, for the setup hub's BACKGROUND_VERT icon.
    vw = int(H * 0.6)
    vert = img.crop((980 - vw // 2, 0, 980 + vw // 2, H))
    vert.save(OUT_VERT, optimize=True)
    print(f'wrote {os.path.relpath(OUT_VERT, MOD)} ({vw}x{H})')


if __name__ == '__main__':
    main()
