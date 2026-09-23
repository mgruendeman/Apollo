"""Turn the raw film-roll scans into web photos.

The NASA JSC / Arizona State University scans (public domain) show the whole
strip of film: sprocket holes down both sides, the black film edge, and
slivers of the neighbouring frames above and below. The picture is the
square in the middle. For each frame this:

  1. downloads the scan ("med" is about 3,550 x 4,000 px, 14-18 MB PNG;
     "small" is 1,100 px wide), skipping files already downloaded;
  2. crops to the picture: a centred square 76.7% of the scan's width,
     moved to line up with the frame's edges where they're clearly visible
     (black lunar sky hides them, so otherwise it stays centred), then
     trimmed by a small margin;
  3. trims any leftover black film edge along the sides;
  4. gently stretches the levels (the scans are flat), keeping colour;
  5. takes out most of the tint the film has picked up with age (see
     film_tint; --tint-strength 0 turns this off), and applies a small
     tone curve close to NASA's own processing (--no-tone-curve to skip);
  6. writes a 2048 px JPEG for the lightbox and a 400 px thumbnail.

    python3 pipeline/process_photos.py --mission 11 --limit 20 --size small --out ~/apollo-media/photos
    python3 pipeline/process_photos.py --frames AS11-40-5875 AS08-14-2383 --preview sheet.jpg

Needs: pip install pillow numpy
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).parent.parent
ARCHIVE = 'https://tothemoon.im-ldi.com'
SIDE = 0.767      # picture width as a share of the scan's width
MARGIN = 0.03     # trimmed inside the frame edge
WEB_PX, THUMB_PX = 2048, 400
SRGB_TO_XYZ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
D65 = np.array([0.95047, 1.0, 1.08883])
MID_GAMMA, SHOULDER = 0.85, 0.12   # tone_curve
MAX_TINT, KEEP_TINT = 45, 3        # film_tint, adjust_colour (L*a*b* units)


def scan_url(frame_id, fmt, size):
    roll = frame_id[:4].upper()
    if fmt == 'b':  # 35 mm Nikon scans
        return f"{ARCHIVE}/data_a/{roll}/png/{frame_id}_{'SML' if size == 'small' else 'MED'}.png"
    return f'{ARCHIVE}/data_a70/{roll}/extra/{frame_id}.{size}.png'


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            data = urllib.request.urlopen(url, timeout=300).read()
            tmp = dest.with_suffix('.part')
            tmp.write_bytes(data)
            tmp.rename(dest)
            return dest
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def load_rgb(path):
    im = Image.open(path)
    if im.mode.startswith('I'):  # 16-bit greyscale scans
        a = (np.asarray(im, dtype=np.float32) / 256).clip(0, 255).astype(np.uint8)
        im = Image.fromarray(a)
    return im.convert('RGB')


def frame_box(im):
    """(left, top, right, bottom) of the picture inside the scanned strip."""
    w, h = im.size
    side = SIDE * w
    left = (w - side) / 2
    top = (h - side) / 2
    # Refine the position from the frame's edges: strong steps in brightness
    # near where the geometry expects them, the right distance apart. Black
    # lunar sky hides an edge, in which case that axis stays centred.
    g = np.asarray(im.convert('L'), dtype=np.float32)
    rows = np.abs(np.diff(g[:, int(w * 0.3):int(w * 0.7)], axis=0)).mean(1)
    cols = np.abs(np.diff(g[int(h * 0.3):int(h * 0.7)], axis=1)).mean(0)

    def refine(profile, start, length, span):
        win = int(0.05 * span)

        def peak(center):
            lo, hi = max(0, int(center - win)), min(len(profile), int(center + win))
            i = lo + int(np.argmax(profile[lo:hi]))
            return i, profile[i]

        (a, a_s), (b, b_s) = peak(start), peak(start + length)
        strong = np.percentile(profile, 98)
        if a_s >= strong and b_s >= strong and abs((b - a) - length) < 0.04 * span:
            return a
        return start

    top = refine(rows, top, side, h)
    left = refine(cols, left, side, w)
    m = MARGIN * side
    return int(left + m), int(top + m), int(left + side - m), int(top + side - m)


def trim_dark_edges(im, limit=0.03):
    """Remove leftover film edge: uniformly black lines along any side, up
    to `limit` of the size (at worst this trims a sliver of black sky)."""
    g = np.asarray(im.convert('L'), dtype=np.float32)
    h, w = g.shape

    def count(lines, n):
        k = 0
        while k < int(limit * n) and lines[k].mean() < 18 and lines[k].std() < 10:
            k += 1
        return k

    top, bottom = count(g, h), count(g[::-1], h)
    left, right = count(g.T, w), count(g.T[::-1], w)
    return im.crop((left, top, w - right, h - bottom))


def enhance(im):
    # Stretch levels a little (ignoring the extreme 0.5% of pixels), per
    # image not per channel, so the colour balance of the film is kept.
    return ImageOps.autocontrast(im, cutoff=0.5, preserve_tone=True)


def srgb_to_linear(rgb):
    c = rgb / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
    return (np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)


def linear_to_lab(c):
    """Linear sRGB to CIE L*a*b* (D65)."""
    xyz = c @ SRGB_TO_XYZ.T / D65
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_linear(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > 0.2069, f ** 3, (f - 16 / 116) / 7.787) * D65
    return xyz @ np.linalg.inv(SRGB_TO_XYZ).T


def to_lab(rgb):
    return linear_to_lab(srgb_to_linear(rgb))


def film_tint(lab):
    """The colour (L*, a*, b*) of the things in the picture that should be grey
    or white (sunlit soil, suits, cabin panels, clouds), or None.

    Looks at the bright tones first (then mid, then dark tones if a band
    has too few pixels), finds the biggest cluster of similar colours
    there, and takes its colour. None when there is no such cluster (the
    picture is too varied to tell what should be grey) or when the colour
    is too strong to be a tint. NASA's own processed versions have bright
    greys within about 3 units of neutral, while the scans are off by up
    to about 40."""
    L, a, b = (lab[..., i].ravel() for i in range(3))
    for lo, hi in [(60, 97), (30, 65), (15, 35)]:
        m = (L >= lo) & (L < hi)
        if m.sum() < 0.02 * L.size:
            continue
        aa, bb = a[m], b[m]
        ca, cb = np.median(aa), np.median(bb)
        for _ in range(4):
            near = np.hypot(aa - ca, bb - cb) < 12
            if near.sum() < 0.3 * m.sum():
                return None
            ca, cb = np.median(aa[near]), np.median(bb[near])
        cl = np.median(L[m][near])
        return (cl, ca, cb) if 0.5 < np.hypot(ca, cb) <= MAX_TINT else None
    return None


def tone_curve(L):
    """A small tone adjustment on L* (0-100), fitted to NASA's own processed
    versions of 37 frames: mid tones lifted a little (a 0.85 gamma), and
    the brightest tones eased down so sunlit soil and suits aren't glaring
    (white ends up at about 88). Black stays black."""
    x = (np.clip(L, 0, 100) / 100) ** MID_GAMMA * 100
    return x - SHOULDER * 100 * (x / 100) ** 3


def adjust_colour(im, tint_strength, tone=True):
    """Remove the film's tint, then apply tone_curve.

    The tint is taken out as a white balance: one gain per colour channel
    in linear light, chosen so the picture's greys come out neutral. Like
    the film's own cast, that correction is strongest in the bright tones
    and fades towards black. `tint_strength` 0.75 removes 75% of a small
    tint and all but KEEP_TINT units of a large one, so a hint of the
    film's warmth stays and it never looks over-corrected."""
    tint = None
    if tint_strength > 0:
        small = im.copy()
        small.thumbnail((800, 800))
        tint = film_tint(to_lab(np.asarray(small, dtype=np.float32)))
    if not tint and not tone:
        return im
    lin = srgb_to_linear(np.asarray(im, dtype=np.float32))
    if tint:
        cl, ca, cb = tint
        keep = min(1 - tint_strength, KEEP_TINT / np.hypot(ca, cb))
        grey, target = lab_to_linear(np.array([[cl, ca, cb], [cl, ca * keep, cb * keep]]))
        lin = lin * (target / np.maximum(grey, 1e-6))
    if not tone:
        return Image.fromarray(linear_to_srgb(lin))
    lab = linear_to_lab(lin)
    lab[..., 0] = tone_curve(lab[..., 0])
    return Image.fromarray(linear_to_srgb(lab_to_linear(lab)))


def process(frame_id, fmt, size, work, out, tint_strength=0.75, tone=True):
    src = download(scan_url(frame_id, fmt, size), work / size / f'{frame_id}.png')
    if not src:
        return None, 'download failed'
    im = load_rgb(src)
    box = frame_box(im) if fmt == 'a' else None
    pic = enhance(trim_dark_edges(im.crop(box)) if box else im)
    out.mkdir(parents=True, exist_ok=True)
    web = pic.copy()
    web.thumbnail((WEB_PX, WEB_PX), Image.LANCZOS)
    web = adjust_colour(web, tint_strength, tone)
    web.save(out / f'{frame_id}.jpg', quality=85, optimize=True, progressive=True)
    thumb = web.copy()
    thumb.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
    thumb.save(out / f'{frame_id}.thumb.jpg', quality=80, optimize=True)
    return (im, box), 'ok'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mission', help='mission number, e.g. 11 (frames from public/photo-index)')
    ap.add_argument('--frames', nargs='*', help='specific frame ids, e.g. AS11-40-5875')
    ap.add_argument('--limit', type=int, default=0, help='only the first N frames (0 = all)')
    ap.add_argument('--size', choices=['small', 'med'], default='med')
    ap.add_argument('--work', default='~/apollo-media/scans', help='where downloaded scans are kept')
    ap.add_argument('--out', default='~/apollo-media/photos')
    ap.add_argument('--tint-strength', type=float, default=0.75,
                    help='how much of the film\'s age tint to remove (0 = off, 1 = all)')
    ap.add_argument('--no-tone-curve', action='store_true', help='skip the small tone adjustment')
    ap.add_argument('--preview', help='also write a contact sheet showing each crop box')
    args = ap.parse_args()
    work, out = Path(args.work).expanduser(), Path(args.out).expanduser()

    rows = []
    if args.mission:
        index = json.loads((ROOT / 'public' / 'photo-index' / f'{int(args.mission):02d}.json').read_text())
        rows = [(r[0], r[1]) for r in index['frames']]
    if args.frames:
        rows += [(f, 'a') for f in args.frames]
    if args.limit:
        rows = rows[:args.limit]

    previews = []
    for n, (fid, fmt) in enumerate(rows, 1):
        result, status = process(fid, fmt, args.size, work, out, args.tint_strength, not args.no_tone_curve)
        print(f'[{n}/{len(rows)}] {fid}: {status}', flush=True)
        if result and args.preview:
            im, box = result
            p = im.copy()
            if box:
                ImageDraw.Draw(p).rectangle(box, outline=(255, 0, 0), width=max(3, im.size[0] // 150))
            p.thumbnail((300, 340))
            previews.append(p)
    if previews:
        cols = 6
        sheet = Image.new('RGB', (300 * cols, 340 * ((len(previews) + cols - 1) // cols)))
        for i, p in enumerate(previews):
            sheet.paste(p, (300 * (i % cols), 340 * (i // cols)))
        sheet.save(Path(args.preview).expanduser(), quality=85)


if __name__ == '__main__':
    main()
