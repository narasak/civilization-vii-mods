#!/usr/bin/env python3
"""One Steam Workshop preview layout for every mod in this repository, so they read as one author's work.

  python3 tools/workshop_preview.py <mod-folder> "<Thai title>" "<English name>" "<Thai subtitle>" [background.png]

The optional background (centre-cropped to a square, shaded so the text stays readable) replaces the
navy gradient; text, rule and frame never move.

Writes <mod-folder>/workshop/preview.png (1024x1024) and preview-512.png (the official Uploader's
recommended size). Layout first drawn for the Thai Language Pack (2026-11-06); fonts are that mod's
bundled Kanit and Sarabun. Needs Pillow with libraqm: without OpenType shaping Thai tone marks collide
with upper vowels (seen on the Thai pack's v12 image, 2026-11-12), so the script refuses to run.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(REPO, 'thai-language', 'fonts')
W = H = 1024
NAVY, GOLD, PALE, DIM = (17, 20, 28), (214, 182, 120), (232, 226, 212), (150, 156, 170)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size, layout_engine=ImageFont.Layout.RAQM)


def draw(title, name, subtitle, background=None):
    img = Image.new('RGB', (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for i in range(H):  # soft vertical gradient
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(17 + 14 * t), int(20 + 12 * t), int(28 + 18 * t)))
    if background:
        bg = Image.open(background).convert('RGB')
        side = min(bg.size)
        bg = bg.crop(((bg.width - side) // 2, (bg.height - side) // 2,
                      (bg.width + side) // 2, (bg.height + side) // 2)).resize((W, H), Image.LANCZOS)
        shade = Image.new('RGBA', (W, H))
        ds = ImageDraw.Draw(shade)
        for i in range(H):  # darkest behind the text block, lighter over the skyline
            a = int(110 - 90 * min(1, max(0, i - 120) / 760))
            ds.line([(0, i), (W, i)], fill=NAVY + (a,))
        img = Image.alpha_composite(bg.convert('RGBA'), shade).convert('RGB')
        d = ImageDraw.Draw(img)
    d.rectangle([28, 28, W - 29, H - 29], outline=GOLD, width=3)
    d.rectangle([44, 44, W - 45, H - 45], outline=(102, 90, 69), width=2)

    def center(y, text, f, fill):
        nonlocal img, d
        w = d.textlength(text, font=f)
        if background:  # a soft shadow keeps the text readable over the picture
            glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(glow).text(((W - w) / 2, y + 4), text, font=f, fill=(0, 0, 0, 230))
            img = Image.alpha_composite(img.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(9))).convert('RGB')
            d = ImageDraw.Draw(img)
        d.text(((W - w) / 2, y), text, font=f, fill=fill)

    center(150, 'CIVILIZATION VII', font('lth-Kanit-Medium.ttf', 52), DIM)
    center(300, title, font('lth-Kanit-SemiBold.ttf', 230), GOLD)
    d.line([(312, 640), (712, 640)], fill=GOLD, width=3)
    center(675, name, font('lth-Kanit-SemiBold.ttf', 84), PALE)
    center(800, subtitle, font('lth-Sarabun-SemiBold.ttf', 46), DIM)
    return img


def main(argv):
    if len(argv) not in (5, 6):
        sys.exit(__doc__)
    if not features.check('raqm'):
        sys.exit('Pillow has no libraqm: Thai marks would collide. Install a Pillow wheel with raqm.')
    mod, title, name, subtitle = argv[1:5]
    background = argv[5] if len(argv) == 6 else None
    out = os.path.join(mod, 'workshop')
    os.makedirs(out, exist_ok=True)
    img = draw(title, name, subtitle, background)
    img.save(os.path.join(out, 'preview.png'), optimize=True)
    img.resize((512, 512), Image.LANCZOS).save(os.path.join(out, 'preview-512.png'), optimize=True)
    print(f'wrote {out}/preview.png and preview-512.png')


if __name__ == '__main__':
    main(sys.argv)
