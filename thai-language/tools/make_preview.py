#!/usr/bin/env python3
"""Draw the Steam Workshop preview image (workshop/preview.png, 1024x1024) with the mod's own fonts."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, features

# Thai needs OpenType shaping: without libraqm Pillow's basic layout stacks a tone mark on top of an
# upper vowel (the mai tho collided with the mai han-akat in "ทั้ง" on the v12 Workshop image, 2026-11-12).
if not features.check('raqm'):
    sys.exit('Pillow has no libraqm: Thai marks would collide. Install a Pillow wheel with raqm.')
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda name, size: ImageFont.truetype(os.path.join(MOD, 'fonts', name), size,
                                          layout_engine=ImageFont.Layout.RAQM)
W = H = 1024
NAVY, GOLD, PALE, DIM = (17, 20, 28), (214, 182, 120), (232, 226, 212), (150, 156, 170)

img = Image.new('RGB', (W, H), NAVY)
d = ImageDraw.Draw(img)
for i in range(H):  # soft vertical gradient
    t = i / H
    d.line([(0, i), (W, i)], fill=(int(17 + 14 * t), int(20 + 12 * t), int(28 + 18 * t)))
d.rectangle([28, 28, W - 29, H - 29], outline=GOLD, width=3)
d.rectangle([44, 44, W - 45, H - 45], outline=(102, 90, 69), width=2)


def center(y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


center(150, 'CIVILIZATION VII', F('lth-Kanit-Medium.ttf', 52), DIM)
center(300, 'ภาษาไทย', F('lth-Kanit-SemiBold.ttf', 230), GOLD)
d.line([(312, 640), (712, 640)], fill=GOLD, width=3)
center(675, 'Thai Language Pack', F('lth-Kanit-SemiBold.ttf', 84), PALE)
center(800, 'แปลทั้งเกม  ·  ทุกยุค  ·  ทุก DLC', F('lth-Sarabun-SemiBold.ttf', 46), DIM)

out = os.path.join(MOD, 'workshop', 'preview.png')
img.save(out, optimize=True)
print(out, os.path.getsize(out), 'bytes')
small = os.path.join(MOD, 'workshop', 'preview-512.png')  # the Workshop Uploader's recommended size
img.resize((512, 512), Image.LANCZOS).save(small, optimize=True)
print(small, os.path.getsize(small), 'bytes')
