#!/usr/bin/env python3
"""The missions' official emblems (crew patches) for the home page's cards:
NASA's artwork, fetched from NASA, the white around each patch cut away,
trimmed and scaled.

    python3 scripts/make_patches.py

Writes src/assets/patches/apolloNN.webp. The sources are listed in
src/data/patches.js too, for the credit.
"""
import io
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent.parent / 'src' / 'assets' / 'patches'
LONG_SIDE = 192   # px; the cards show them at about 64 px

# NASA photo numbers, from NASA's image library (images.nasa.gov) or, for
# Apollo 8 and 10, NASA's "Human Spaceflight Mission Patches" gallery.
SOURCES = {
    '08': 'https://www.nasa.gov/wp-content/uploads/2017/12/s68-51093.jpg',
    '09': 'https://images-assets.nasa.gov/image/S69-18569/S69-18569~large.jpg',
    '10': 'https://www.nasa.gov/wp-content/uploads/2019/05/apollo_10_patch_s69-31959.jpg',
    '11': 'https://images-assets.nasa.gov/image/S69-34875/S69-34875~large.jpg',
    '12': 'https://images-assets.nasa.gov/image/S69-52336/S69-52336~large.jpg',
    '13': 'https://images-assets.nasa.gov/image/S69-60662/S69-60662~large.jpg',
    '14': 'https://images-assets.nasa.gov/image/S70-17851/S70-17851~large.jpg',
    '15': 'https://images-assets.nasa.gov/image/S71-30463/S71-30463~large.jpg',
    '16': 'https://images-assets.nasa.gov/image/S71-56246/S71-56246~large.jpg',
    '17': 'https://images-assets.nasa.gov/image/s72-49079/s72-49079~large.jpg',
}


def cut_white(rgb):
    """The patch without the white paper around it: near-white reached from
    the edges (the patches have a coloured border all round, so the fill
    stops there). Returns alpha, 0-1, softened a touch at the edge."""
    a = rgb.astype(int)
    white = (a.min(axis=2) >= 232) & (a.max(axis=2) - a.min(axis=2) <= 18)
    parts, _ = ndimage.label(white)
    edge = set(np.unique(np.concatenate([parts[0], parts[-1], parts[:, 0], parts[:, -1]]))) - {0}
    back = np.isin(parts, list(edge))
    back = ndimage.binary_dilation(back, iterations=1) & white | back   # (jpeg fringe next to the paper)
    return ndimage.gaussian_filter((~back).astype(float), 1.0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for mission, url in SOURCES.items():
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=120).read())).convert('RGB')
        im.thumbnail((1200, 1200), Image.LANCZOS)   # (Apollo 8's is 6187 px)
        rgb = np.asarray(im)
        alpha = cut_white(rgb)
        rgba = np.dstack([rgb, (alpha * 255).round().astype(np.uint8)])
        ys, xs = np.nonzero(alpha > 0.03)
        out = Image.fromarray(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 'RGBA')
        out.thumbnail((LONG_SIDE, LONG_SIDE), Image.LANCZOS)
        path = OUT / f'apollo{mission}.webp'
        out.save(path, 'WEBP', quality=88, method=6)
        print(f'{path.name}: {out.width}x{out.height}, {path.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
