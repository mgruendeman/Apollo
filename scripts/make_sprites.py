#!/usr/bin/env python3
"""Cut the diagram's cartoon sprites to size: transparent, trimmed, WebP.

    python3 scripts/make_sprites.py NAME=SOURCE.png[:pockets] [...]

Writes src/assets/sprites/NAME.webp. A source with real transparency is
just trimmed and scaled. One whose "transparency" is a grey checkerboard
drawn into the pixels (as AI image tools often export) has it cut out:
the checkerboard is grey and the drawings have a dark outline all round,
so grey is flood-filled from the edges up to the outline. With ':pockets',
grey pockets the fill can't reach (between a leg and its strut) go too
when they look like checkerboard rather than paint: tones that alternate
at the squares' spacing and stay neutral grey (the drawing's own whites
are warm cream, and its shadows flat). Some pockets carry the drawing's
blue glow, which dulls the squares; those count on less texture.

Special names: 'lm' also writes lm-ascent.webp and lm-descent.webp, the
two stages cut apart where the white cabin meets the gold descent stage.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent.parent / 'src' / 'assets' / 'sprites'
LONG_SIDE = 256   # px; the diagram draws its largest sprite about 60 px wide, so this covers 3x screens


def _texture(lum, region):
    """Share of the region's pixel pairs a checker square apart (10-13 px,
    across or down) that differ sharply in tone: high for checkerboard."""
    best = 0
    for d in (10, 11, 12, 13):
        for dy, dx in ((0, d), (d, 0)):
            both = region[:region.shape[0] - dy, :region.shape[1] - dx] & region[dy:, dx:]
            if both.sum() < 50:
                continue
            diff = np.abs(lum[:lum.shape[0] - dy, :lum.shape[1] - dx] - lum[dy:, dx:])[both]
            best = max(best, (diff > 45).mean())
    return best


def cut_checkerboard(rgb, pockets=False):
    a = rgb.astype(int)
    lum = a.mean(axis=2)
    sat = a.max(axis=2) - a.min(axis=2)
    grey = (sat <= 28) & (lum >= 95) & (lum <= 232)
    # close pinholes in the outline so the fill can't leak through them
    wall = ndimage.binary_dilation(~grey, iterations=2)
    open_grey = grey & ~wall
    parts, n = ndimage.label(open_grey)
    edge = set(np.unique(np.concatenate([parts[0], parts[-1], parts[:, 0], parts[:, -1]]))) - {0}
    back = np.isin(parts, list(edge))
    if pockets:
        sizes = ndimage.sum(np.ones_like(lum), parts, range(1, n + 1))
        for k in range(1, n + 1):
            if k in edge or sizes[k - 1] < 60:
                continue
            region = parts == k
            tex, px = _texture(lum, region), a[region]
            neutral = np.median(sat[region]) <= 10
            blue = (px[:, 0] - px[:, 2]).mean() <= -10
            if (tex >= 0.25 and neutral) or (tex >= 0.15 and blue):
                back |= region
    back = grey & ndimage.binary_dilation(back, iterations=3)   # reclaim the margin the wall took
    # specks left over from the checkerboard's smudges (not grey enough to
    # count as background) stand apart from the drawing: drop them
    keep, n = ndimage.label(~back)
    sizes = ndimage.sum(np.ones_like(lum), keep, range(1, n + 1))
    return np.isin(keep, 1 + np.nonzero(sizes >= 0.005 * sizes.max())[0])


def finish(rgba, name):
    alpha = rgba[..., 3]
    ys, xs = np.nonzero(alpha > 8)
    rgba = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(rgba, 'RGBA')
    scale = LONG_SIDE / max(im.size)
    if scale < 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{name}.webp'
    im.save(path, 'WEBP', quality=88, method=6)
    print(f'{path.name}: {im.width}x{im.height}, {path.stat().st_size // 1024} KB')


def main():
    for arg in sys.argv[1:]:
        name, src = arg.split('=', 1)
        src, _, opt = src.partition(':')
        im = Image.open(src)
        if im.mode == 'RGBA' and np.asarray(im)[..., 3].min() == 0:
            rgba = np.asarray(im).copy()
        else:
            rgb = np.asarray(im.convert('RGB'))
            keep = cut_checkerboard(rgb, pockets=opt == 'pockets')
            alpha = ndimage.gaussian_filter(keep.astype(float), 0.8)   # soften the cut edge a touch
            rgba = np.dstack([rgb, (alpha * 255).round().astype(np.uint8)])
        finish(rgba, name)
        if name == 'lm':
            # the cabin is white/grey, the descent stage gold: find the band where
            # gold fills most of the width, then cut where the gold begins above it
            a = rgba.astype(int)
            gold = (a[..., 0] - a[..., 2] > 60) & (a[..., 3] > 128)
            rows = gold.sum(axis=1)
            opaque = (a[..., 3] > 128).sum(axis=1)
            top = np.nonzero(opaque)[0][0]
            band = next(y for y in range(top + (len(rows) - top) // 3, len(rows)) if rows[y] > 0.35 * max(opaque[y], 1))
            cut = band
            while cut > top and rows[cut - 1] > 0.01 * a.shape[1]:
                cut -= 1
            # in this three-quarter view the stage's top shows between the cabin's
            # lower edges; clear gold from the ascent stage's bottom band
            ascent = rgba[:cut].copy()
            low = ascent[int(cut - 0.2 * (cut - top)):]
            warm = low[..., 0].astype(int) - low[..., 2].astype(int) > 45
            low[warm, 3] = 0
            finish(ascent, 'lm-ascent')
            finish(rgba[cut:].copy(), 'lm-descent')


if __name__ == '__main__':
    main()
