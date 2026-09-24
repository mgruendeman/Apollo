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
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
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
# A reviewer's dials (tone_curve, adjust_colour); the review page matches.
BRIGHTNESS_STEP, CONTRAST_STEP, TONE_STEP = 0.8 ** 0.5, 0.55, 10
SATURATION_STEP, COLOUR_STEP = 0.1, 1.5
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
        except urllib.error.HTTPError as e:
            if e.code == 404:   # not in the archive: retrying won't help
                return None
            time.sleep(5 * (attempt + 1))
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

    def refine(profile, start, length, span, reach):
        win = int(reach * span)

        def peak(center):
            lo, hi = max(0, int(center - win)), min(len(profile), int(center + win))
            i = lo + int(np.argmax(profile[lo:hi]))
            return i, profile[i]

        (a, a_s), (b, b_s) = peak(start), peak(start + length)
        strong = np.percentile(profile, 98)
        if a_s >= strong and b_s >= strong and abs((b - a) - length) < 0.04 * span:
            return a
        return start

    # Along the roll, frame spacing varies, so look further; across it the
    # sprocket holes fix the position (a wider search finds their edges).
    top = refine(rows, top, side, h, 0.08)
    left = refine(cols, left, side, w, 0.05)
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


def tone_curve(L, brightness=0, contrast=0, shadows=0, highlights=0):
    """The tone adjustment on L* (0-100). By default: mid tones lifted a
    little (a 0.85 gamma), and the brightest tones eased down so sunlit
    soil and suits aren't glaring (white ends up at about 88), fitted to
    NASA's own processed versions of 37 frames. Black stays black.

    The other arguments are a reviewer's dials, -8 to +8 steps each:
      brightness  one step moves mid grey about 3.5 L*
      contrast    an S-curve (tanh) keeping black and white fixed; one step
                  moves the quarter tones about 2.5 apart
      shadows     lifts (+) or deepens (-) the dark tones, about 1.5 per step
      highlights  brightens (+) or tones down (-) the bright tones, the same
    Every combination stays monotonic (no tone reversals). The review page
    previews with the same formulas, so keep the two in step."""
    x = (np.clip(L, 0, 100) / 100) ** (MID_GAMMA * BRIGHTNESS_STEP ** brightness) * 100
    if contrast:
        k = CONTRAST_STEP * abs(contrast)
        d = (x - 50) / 50
        d = np.tanh(k * d) / np.tanh(k) if contrast > 0 else np.arctanh(np.clip(d, -1, 1) * np.tanh(k)) / k
        x = 50 + 50 * d
    x = x - SHOULDER * 100 * (x / 100) ** 3
    if shadows or highlights:
        t = x / 100
        x = x + TONE_STEP * (shadows * t * (1 - t) ** 2 + highlights * (1 - t) * t * t)
    return x


def adjust_colour(im, tint_strength, tone=True, review=None):
    """Remove the film's tint, apply tone_curve, then a reviewer's colour
    dials.

    The tint is taken out as a white balance: one gain per colour channel
    in linear light, chosen so the picture's greys come out neutral. Like
    the film's own cast, that correction is strongest in the bright tones
    and fades towards black. `tint_strength` 0.75 removes 75% of a small
    tint and all but KEEP_TINT units of a large one, so a hint of the
    film's warmth stays and it never looks over-corrected.

    Colour dials (-8 to +8): saturation scales colourfulness by 10% a step
    (-8 is nearly black and white); warmth moves colours towards yellow (+)
    or blue (-), tint towards magenta (+) or green (-), 1.5 a*/b* units a
    step, fading out at pure black and white."""
    review = review or {}
    tint = None
    if tint_strength > 0:
        small = im.copy()
        small.thumbnail((800, 800))
        tint = film_tint(to_lab(np.asarray(small, dtype=np.float32)))
    dials = any(review.get(k) for k in ('saturation', 'warmth', 'tint'))
    if not tint and not tone and not dials:
        return im
    lin = srgb_to_linear(np.asarray(im, dtype=np.float32))
    if tint:
        cl, ca, cb = tint
        keep = min(1 - tint_strength, KEEP_TINT / np.hypot(ca, cb))
        grey, target = lab_to_linear(np.array([[cl, ca, cb], [cl, ca * keep, cb * keep]]))
        lin = lin * (target / np.maximum(grey, 1e-6))
    if not tone and not dials:
        return Image.fromarray(linear_to_srgb(lin))
    lab = linear_to_lab(lin)
    L0 = lab[..., 0].copy()
    if dials:
        fade = np.clip(L0 / 10, 0, 1) * np.clip((100 - L0) / 5, 0, 1)
        sat = 1 + SATURATION_STEP * review.get('saturation', 0)
        lab[..., 1] = lab[..., 1] * sat + COLOUR_STEP * review.get('tint', 0) * fade
        lab[..., 2] = lab[..., 2] * sat + COLOUR_STEP * review.get('warmth', 0) * fade
    if tone:
        lab[..., 0] = tone_curve(L0, *(review.get(k, 0) for k in ('brightness', 'contrast', 'shadows', 'highlights')))
    return Image.fromarray(linear_to_srgb(lab_to_linear(lab)))


def straighten(im, degrees):
    """Turn by a small angle (clockwise) and crop to the largest centred
    rectangle of the same shape that has no empty corners."""
    if not degrees:
        return im
    w, h = im.size
    th = np.radians(abs(degrees))
    k = np.cos(th) + max(w / h, h / w) * np.sin(th)
    im = im.rotate(-degrees, resample=Image.BICUBIC)
    cw, ch = w / k, h / k
    return im.crop((round((w - cw) / 2), round((h - ch) / 2), round((w + cw) / 2), round((h + ch) / 2)))


def process(frame_id, fmt, size, work, out, tint_strength=0.75, tone=True, review=None,
            preview=False, discard=False):
    """Download (if needed) and process one frame. Returns (status, a small
    crop-check image when `preview`)."""
    review = review or {}
    src = download(scan_url(frame_id, fmt, size), work / size / f'{frame_id}.png')
    if not src and size == 'med':   # some 35 mm frames (e.g. the stereo close-ups) only have a small scan
        src = download(scan_url(frame_id, fmt, 'small'), work / 'small' / f'{frame_id}.png')
    if not src:
        return 'download failed', None
    im = load_rgb(src)
    box = frame_box(im) if fmt == 'a' else None
    pic = enhance(trim_dark_edges(im.crop(box)) if box else im)
    turn = review.get('rotate', 0) % 360   # a reviewer's rotation, degrees clockwise
    if turn:
        pic = pic.rotate(-turn, expand=True)
    pic = straighten(pic, review.get('straighten', 0))
    out.mkdir(parents=True, exist_ok=True)
    web = pic.copy()
    web.thumbnail((WEB_PX, WEB_PX), Image.LANCZOS)
    web = adjust_colour(web, tint_strength, tone, review)
    web.save(out / f'{frame_id}.jpg', quality=85, optimize=True, progressive=True)
    thumb = web.copy()
    thumb.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
    thumb.save(out / f'{frame_id}.thumb.jpg', quality=80, optimize=True)
    sheet = None
    if preview:
        sheet = im.copy()
        if box:
            ImageDraw.Draw(sheet).rectangle(box, outline=(255, 0, 0), width=max(3, im.size[0] // 150))
        sheet.thumbnail((300, 340))
    if discard:
        src.unlink(missing_ok=True)
    return 'ok', sheet


def nasa_released():
    """Frame keys NASA's Image Library has its own version of (the site
    shows NASA's, so these don't need our cleanup)."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from fetch_archive_frames import frame_key
    photos = json.loads((ROOT / 'src' / 'data' / 'missionPhotos.json').read_text())
    return frame_key, {frame_key(p['id']) for ps in photos.values() for p in ps if frame_key(p['id'])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--missions', '--mission', nargs='+', default=[], help='mission numbers, e.g. 8 11 (frames from public/photo-index)')
    ap.add_argument('--frames', nargs='*', help='specific frame ids, e.g. AS11-40-5875')
    ap.add_argument('--limit', type=int, default=0, help='only the first N frames per mission (0 = all)')
    ap.add_argument('--size', choices=['small', 'med'], default='med')
    ap.add_argument('--work', default='~/apollo-media/scans', help='where downloaded scans are kept')
    ap.add_argument('--out', default='~/apollo-media/photos', help='output folder (one subfolder per mission)')
    ap.add_argument('--workers', type=int, default=2, help='photos processed at once (each uses a CPU core and ~1 GB of memory)')
    ap.add_argument('--discard-scans', action='store_true', help='delete each scan once processed (needs ~11 GB, not ~300 GB; '
                                                                   're-running a photo downloads its scan again)')
    ap.add_argument('--include-nasa', action='store_true', help='also process frames NASA released its own version of')
    ap.add_argument('--force', action='store_true', help='redo photos that are already done')
    ap.add_argument('--tint-strength', type=float, default=0.75,
                    help='how much of the film\'s age tint to remove (0 = off, 1 = all)')
    ap.add_argument('--no-tone-curve', action='store_true', help='skip the tone curve (and reviewers\' tone dials)')
    ap.add_argument('--reviews', help='reviewers\' marks (see README): dials are applied, colour and crop marks '
                                      'are listed for a hand fix; reviewed photos are always redone')
    ap.add_argument('--only-reviewed', action='store_true', help='with --reviews: process just the reviewed frames')
    ap.add_argument('--preview', help='also write a contact sheet showing each crop box')
    args = ap.parse_args()
    work, out = Path(args.work).expanduser(), Path(args.out).expanduser()
    reviews = json.loads(Path(args.reviews).expanduser().read_text()) if args.reviews else {}

    rows = []
    for m in args.missions:
        index = json.loads((ROOT / 'public' / 'photo-index' / f'{int(m):02d}.json').read_text())
        rows += [(r[0], r[1]) for r in index['frames']][:args.limit or None]
    if args.frames:   # look each one up in its mission's index for its scan type
        fmt = {}
        for m in {f[2:4] for f in args.frames}:
            path = ROOT / 'public' / 'photo-index' / f'{m}.json'
            if path.exists():
                fmt.update({r[0]: r[1] for r in json.loads(path.read_text())['frames']})
        rows += [(f, fmt.get(f, 'a')) for f in args.frames]
    if args.only_reviewed:
        rows = [r for r in rows if r[0] in reviews] if rows else [(f, 'a') for f in reviews]
    if not args.include_nasa:
        key, released = nasa_released()
        before = len(rows)
        rows = [r for r in rows if key(r[0]) not in released or r[0] in reviews]
        if before - len(rows):
            print(f'skipping {before - len(rows)} frames NASA released its own version of (--include-nasa to process them)')
    mission_dir = lambda fid: out / fid[2:4]
    todo = [r for r in rows if args.force or r[0] in reviews or not (mission_dir(r[0]) / f'{r[0]}.jpg').exists()]
    if len(todo) < len(rows):
        print(f'{len(rows) - len(todo)} photos already done (--force to redo them)')
    if not todo:
        return

    hand_fix, previews, failed = [], [], []
    start = time.time()
    tone = not args.no_tone_curve
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        jobs = {pool.submit(process, fid, fmt, args.size, work, mission_dir(fid), args.tint_strength, tone,
                            reviews.get(fid), bool(args.preview), args.discard_scans): fid for fid, fmt in todo}
        for n, job in enumerate(as_completed(jobs), 1):
            fid = jobs[job]
            try:
                status, sheet = job.result()
            except Exception as e:   # a damaged scan shouldn't stop a long run
                status, sheet = f'failed: {e}', None
            if status != 'ok':
                failed.append(fid)
            if sheet:
                previews.append(sheet)
            review = reviews.get(fid) or {}
            if review.get('colour') or review.get('crop'):
                needs = [k for k in ('colour', 'crop') if review.get(k)]
                hand_fix.append(f"{fid}\t{', '.join(needs)}\t{review.get('note', '')}")
            left = (time.time() - start) / n * (len(todo) - n)
            print(f'[{n}/{len(todo)}] {fid}: {status}   (about {left / 3600:.1f} h left)', flush=True)
    if failed:
        print(f'{len(failed)} failed (run the same command again to retry): {" ".join(failed[:20])}')
    if hand_fix:
        path = out / 'needs-hand-fix.tsv'
        path.write_text('frame\tneeds\tnote\n' + '\n'.join(sorted(hand_fix)) + '\n')
        print(f'{len(hand_fix)} frames marked for a colour or crop fix by hand: {path}')
    if previews:
        cols = 6
        sheet = Image.new('RGB', (300 * cols, 340 * ((len(previews) + cols - 1) // cols)))
        for i, p in enumerate(previews):
            sheet.paste(p, (300 * (i % cols), 340 * (i // cols)))
        sheet.save(Path(args.preview).expanduser(), quality=85)


if __name__ == '__main__':
    main()
