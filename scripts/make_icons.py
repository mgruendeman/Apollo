#!/usr/bin/env python3
"""The site's icons, from the small logo (the Moon and a tape reel) in
art/logo/icon.png (not in git: a copy is on the media drive, <media>/art/logo):

    python3 scripts/make_icons.py

Writes to public/: favicon.ico (16, 32 and 48 px, the browser tab),
icon-192.png and icon-512.png (the web manifest's, for a phone's home
screen), and apple-touch-icon.png (180 px on the site's night background:
iOS fills a see-through icon with black).
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'art' / 'logo' / 'icon.png'
OUT = ROOT / 'public'
NIGHT = (5, 7, 13, 255)   # --bg in src/index.css


def square(im, margin=0.0):
    """The logo cropped to what's drawn, centred on a square with `margin`
    (a share of the side) left clear around it."""
    im = im.crop(im.getbbox())
    side = round(max(im.size) / (1 - 2 * margin))
    out = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    out.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    return out


def main():
    logo = Image.open(SRC).convert('RGBA')
    tab = square(logo)
    tab.save(OUT / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    for n in (192, 512):
        square(logo, 0.04).resize((n, n), Image.LANCZOS).save(OUT / f'icon-{n}.png', optimize=True)
    apple = Image.new('RGBA', (180, 180), NIGHT)
    apple.alpha_composite(square(logo, 0.1).resize((180, 180), Image.LANCZOS))
    apple.convert('RGB').save(OUT / 'apple-touch-icon.png', optimize=True)
    for name in ('favicon.ico', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png'):
        print(f'{name}: {(OUT / name).stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
