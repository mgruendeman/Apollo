"""Add processed photos to the review page.

For each frame it writes the page's images into <site>/img: the cleaned
photo (1400 px), the raw scan (800 px) and a thumbnail, and appends the
frame to frames.json. Run process_photos.py on the frames first.

    python pipeline/review_page/add_batch.py --media $MEDIA --site page/ AS08-13-2242 AS10-27-3882 ...
    python pipeline/review_page/build.py page/photo-review.html
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parent.parent


def load(path):
    im = Image.open(path)
    if im.mode.startswith('I'):   # 16-bit greyscale scans
        im = Image.fromarray((np.asarray(im, dtype=np.float32) / 256).clip(0, 255).astype(np.uint8))
    return im.convert('RGB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames', nargs='+')
    ap.add_argument('--media', required=True, help='folder holding scans/ and photos/ (as process_photos.py wrote them)')
    ap.add_argument('--site', required=True, help='folder the page is published from; images go in its img/')
    ap.add_argument('--batch', type=int, default=0)
    args = ap.parse_args()
    media, img = Path(args.media).expanduser(), Path(args.site).expanduser() / 'img'
    img.mkdir(parents=True, exist_ok=True)

    def save(im, px, name, q=80):
        im = im.copy()
        im.thumbnail((px, px), Image.LANCZOS)
        im.save(img / name, quality=q, optimize=True, progressive=True)
        return f'img/{name}'

    frames = json.loads((HERE / 'frames.json').read_text())
    have = {f['id'] for f in frames}
    index = {}
    for m in {f[2:4] for f in args.frames}:
        for r in json.loads((ROOT / 'public' / 'photo-index' / f'{m}.json').read_text())['frames']:
            index[r[0]] = r
    added = 0
    for fid in args.frames:
        if fid in have:
            continue
        scan = next((p for p in (media / 'scans' / 'med' / f'{fid}.png', media / 'scans' / 'small' / f'{fid}.png') if p.exists()), None)
        photo = media / 'photos' / fid[2:4] / f'{fid}.jpg'
        if not scan or not photo.exists():
            print(f'{fid}: not processed yet, skipped')
            continue
        ours = Image.open(photo)
        row = index.get(fid, [])
        frames.append({'id': fid, 'mission': str(int(fid[2:4])), 'caption': (row[4] or '') if len(row) > 4 else '',
                       'raw': save(load(scan), 800, f'{fid}.raw.jpg', 75), 'ours': save(ours, 1400, f'{fid}.ours.jpg'),
                       'thumb': save(ours, 160, f'{fid}.t.jpg', 78), 'nasa': None, 'batch': args.batch})
        added += 1
    (HERE / 'frames.json').write_text(json.dumps(frames))
    print(f'added {added} frames ({len(frames)} on the page)')


if __name__ == '__main__':
    main()
