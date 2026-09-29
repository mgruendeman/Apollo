#!/usr/bin/env python3
"""The painted spacecraft for the mission diagram, from the artwork in
art/painted/ (saturn.png, chutes.png, lm.png, csm.png, already cut out; the
originals aren't in git: a copy is on the media drive, <media>/art/painted):

    python3 scripts/make_painted_craft.py

Writes src/assets/sprites/*-painted.webp in the poses the diagram draws its
craft in (scripts/make_sprites.py makes the cartoon ones): the Saturn V
upright, the CSM lying nose-left, the LM front-on and split into its ascent
and descent stages, and the docked stack (LM leading, docked to the CSM's
nose) put together from the CSM and LM. NASA's insignia on the returning
capsule is painted out: it's a protected mark, and the real command modules
didn't carry it.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'art' / 'painted'
OUT = ROOT / 'src' / 'assets' / 'sprites'
LONG_SIDE = 256


def load(name):
    im = Image.open(SRC / f'{name}.png').convert('RGBA')
    return im.crop(im.getbbox())


def save(im, name):
    im = im.crop(im.getbbox())
    im.thumbnail((LONG_SIDE, LONG_SIDE), Image.LANCZOS)
    path = OUT / f'{name}-painted.webp'
    im.save(path, 'WEBP', quality=90, method=6)
    print(f'{path.name}: {im.width}x{im.height}')
    return im


def paint_out_insignia(im, centre, radius):
    """Fill the NASA insignia (a blue disc, its red swoosh reaching past it)
    with the capsule's cream: the median of the light panel just around it."""
    a = np.asarray(im).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[:h, :w]
    cx, cy = centre
    d = np.hypot(xx - cx, yy - cy)
    rgb = a[..., :3].astype(int)
    red = (rgb[..., 0] > rgb[..., 1] + 60) & (rgb[..., 0] > 150)
    mask = (d <= radius) | (red & (d <= radius * 1.9))
    ring = (d > radius * 1.2) & (d < radius * 1.5) & (rgb.min(axis=2) > 170)
    a[mask, :3] = np.median(a[ring, :3], axis=0).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def split_lm(lm):
    """The ascent stage (the cabin, above) and the descent stage (the gold
    box and legs): cut where the gold fills the middle of the frame, not
    counting the gold thruster quads out at the sides."""
    a = np.asarray(lm).astype(int)
    h, w = a.shape[:2]
    middle = a[:, w // 4: 3 * w // 4]
    gold = (middle[..., 0] - middle[..., 2] > 70) & (middle[..., 1] > 110) & (middle[..., 3] > 128)
    share = gold.mean(axis=1)
    cut = next(y for y in range(h // 3, h) if share[y] > 0.35)
    while cut > 0 and share[cut - 1] > 0.05:
        cut -= 1
    return lm.crop((0, 0, w, cut)), lm.crop((0, cut, w, h))


def stack(csm_left, lm):
    """The docked stack heading left: the LM, its top turned to face the
    CSM's nose, docked there; the CSM drawn over it (the LM's top antenna
    tucks behind the CSM's cone)."""
    lm_side = lm.rotate(-90, expand=True)   # top now to the right
    # the LM stands about 0.65 the length of the CSM (probe to engine bell)
    k = 0.65 * csm_left.width / lm_side.width
    lm_side = lm_side.resize((round(lm_side.width * k), round(lm_side.height * k)), Image.LANCZOS)
    # docking: the LM's hatch (its top, less the dish antenna) meets the CSM's nose
    overlap = round(0.08 * lm_side.width)
    w = lm_side.width + csm_left.width - overlap
    h = max(lm_side.height, csm_left.height)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(lm_side, (0, (h - lm_side.height) // 2))
    out.alpha_composite(csm_left, (lm_side.width - overlap, (h - csm_left.height) // 2))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    save(load('saturn'), 'saturn')
    chutes = Image.open(SRC / 'chutes.png').convert('RGBA')
    save(paint_out_insignia(chutes, (571, 1150), 45), 'chutes')
    csm_left = load('csm').rotate(90, expand=True)   # nose (up) turned to the left
    save(csm_left, 'csm')
    lm = load('lm')
    save(lm, 'lm')
    ascent, descent = split_lm(lm)
    save(ascent, 'lm-ascent')
    save(descent, 'lm-descent')
    save(stack(csm_left, lm), 'stack')


if __name__ == '__main__':
    main()
