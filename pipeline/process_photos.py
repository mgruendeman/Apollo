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
  5. writes a 2048 px JPEG for the lightbox and a 400 px thumbnail.

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


def process(frame_id, fmt, size, work, out):
    src = download(scan_url(frame_id, fmt, size), work / size / f'{frame_id}.png')
    if not src:
        return None, 'download failed'
    im = load_rgb(src)
    box = frame_box(im) if fmt == 'a' else None
    pic = enhance(trim_dark_edges(im.crop(box)) if box else im)
    out.mkdir(parents=True, exist_ok=True)
    web = pic.copy()
    web.thumbnail((WEB_PX, WEB_PX), Image.LANCZOS)
    web.save(out / f'{frame_id}.jpg', quality=85, optimize=True, progressive=True)
    thumb = pic.copy()
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
        result, status = process(fid, fmt, args.size, work, out)
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
