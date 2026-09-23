"""Build public/photo-index/<mission>.json: every Hasselblad and Nikon frame
in the NASA JSC / Arizona State University "March to the Moon" scan archive
(tothemoon.im-ldi.com), with a rough kind and date for each frame.

The archive gives frame IDs and film magazines but almost no dates or
captions, so each frame inherits the kind and date of the nearest NASA
Image Library photo (src/data/missionPhotos.json, dated and captioned by
NASA) from the same magazine. Magazines with no such photo fall back to the
archive's own short description, or the camera (the lunar-surface data
camera on a landing mission means surface photos).

Blank frames (film leader, fogged or unexposed frames) are dropped by
looking at each thumbnail, and each kept frame gets a 0-9 quality score
from its contrast, so views can prefer the clearest shots.

Output rows: [frameId, format, kind, date, description, quality]
  format 'a' = 70 mm (data_a70/.../extra/ID.thumb.png, .small.png)
         'b' = 35 mm (data_a/.../png/ID_THM.png, _SML.png)
"""
import html
import io
import json
import re
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / 'public' / 'photo-index'
ANCHORS = json.loads((ROOT / 'src' / 'data' / 'missionPhotos.json').read_text())
BASE = 'https://tothemoon.im-ldi.com/gallery/Apollo'
# camera 6: Hasselblad 500EL (spacecraft); 7: 500EL data camera (surface);
# 3: lunar surface closeup camera; 11: Nikon 35 mm
GALLERIES = {
    '08': [6], '09': [6], '10': [6], '11': [6, 7, 3], '12': [6, 7, 3],
    '13': [6], '14': [6, 7, 3], '15': [6, 7], '16': [6, 7, 11], '17': [6, 7, 11],
}
LANDED = {'11', '12', '14', '15', '16', '17'}
SKIP_DESC = re.compile(r'^(blank|no image|dark|darkness|darkness, not plotable)$', re.I)
DESC_KIND = [
    (r'transearth|translunar', 'other'),
    (r'earth|cloud|ocean', 'earth'),
    (r'terminator|lunar (nearside|farside|surface from|orbit)|farside|crater|images of the lunar|sequence|latitude|longitude', 'lunar-orbit'),
    (r'lunar module shadow|flag|seismometer|reflector|surface|rover|lrv|boulder|footprint|thruster|tv camera', 'surface'),
    (r'corona|zodiacal|star', 'other'),
]
ANCHOR_REACH = 30  # frames either side of a NASA photo that inherit it
SURFACE_CAMERAS = {7, 3}
ORBITAL_KINDS = {'earth', 'lunar-orbit', 'interior', 'other'}
THUMB_CACHE = Path('/tmp/apollo-thumb-stats-v2.json')


def frame_key(frame_id):
    m = re.match(r'(?i)(?:KSC-)?AS(\d\d)-0*(\d+[A-D]?)-0*(\d+)', frame_id)
    return (m.group(1), m.group(2).upper(), int(m.group(3))) if m else None


def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ApolloAudioArchive/1.0 (educational project)'})
            return urllib.request.urlopen(req, timeout=240).read().decode('utf-8', 'replace')
        except Exception:
            time.sleep(5 * (attempt + 1))
    return ''


def thumb_url(frame_id, fmt):
    m = frame_id[:4].upper()
    if fmt == 'a':
        return f'https://tothemoon.im-ldi.com/data_a70/{m}/extra/{frame_id}.thumb.png'
    return f'https://tothemoon.im-ldi.com/data_a/{m}/png/{frame_id}_THM.png'


def thumb_stats(args):
    frame_id, fmt = args
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(thumb_url(frame_id, fmt), timeout=60).read()
            im = Image.open(io.BytesIO(data))
            # The 70 mm thumbnails are 16-bit greyscale; Pillow's convert('L')
            # clips those to white, so scale to 0-255 by hand.
            if im.mode.startswith('I'):
                a = np.asarray(im, dtype=float) / 256
            else:
                a = np.asarray(im.convert('L'), dtype=float)
            h, w = a.shape
            # The scans include the film edge; judge the middle of the frame.
            core = a[int(h * 0.2):int(h * 0.8), int(w * 0.2):int(w * 0.8)]
            return frame_id, [round(float(core.mean()), 1), round(float(core.std()), 1)]
        except Exception:
            time.sleep(2 * (attempt + 1))
    return frame_id, None


def is_blank(stats):
    if not stats:
        return False
    mean, std = stats
    return (mean > 225 and std < 18) or (mean < 12 and std < 6)


def classify(cam, mid, near, anchors_in_mag, desc):
    if cam in SURFACE_CAMERAS and mid in LANDED:
        if near and near[1] != 'surface':
            return near[1], near[2]
        return 'surface', near[2] if near else None
    if near and near[1] in ORBITAL_KINDS:
        return near[1], near[2]
    kind = next((kd for pat, kd in DESC_KIND if re.search(pat, desc, re.I)), None)
    if kind and (kind != 'surface' or mid in LANDED):
        return kind, None
    if anchors_in_mag:
        common = Counter(a[1] for a in anchors_in_mag if a[1] in ORBITAL_KINDS).most_common(1)
        if common:
            return common[0][0], None
    # Uncaptioned frames far from any NASA photo: on the lunar missions
    # these are overwhelmingly the Moon seen from orbit (checked by eye on
    # contact sheets); Apollo 9 never left Earth orbit.
    return ('earth' if mid == '09' else 'lunar-orbit'), None


def main():
    stats_cache = json.loads(THUMB_CACHE.read_text()) if THUMB_CACHE.exists() else {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mid, cameras in GALLERIES.items():
        anchors = {}
        for p in ANCHORS.get(mid, []):
            k = frame_key(p['id'])
            if k and k[0] == mid:
                anchors.setdefault(k[1], []).append((k[2], p['kind'], p['date']))
        rows = []
        for cam in cameras:
            page = fetch(f'{BASE}/{int(mid)}/{cam}')
            m = re.search(r'(\[\{&quot;id&quot;.*?\}\])', page, re.S)
            if not m:
                continue
            for f in json.loads(html.unescape(m.group(1))):
                desc = (f.get('subject') or f.get('frame_desc') or '').strip()
                if SKIP_DESC.match(desc):
                    continue
                k = frame_key(f['image_id'])
                if not k:
                    continue
                mag, num = k[1], k[2]
                ranked = sorted(anchors.get(mag, []), key=lambda a: abs(a[0] - num))
                near = ranked[0] if ranked and abs(ranked[0][0] - num) <= ANCHOR_REACH else None
                kind, date = classify(cam, mid, near, anchors.get(mag, []), desc)
                fmt = 'b' if '/data_a/' in (f.get('thumb_image') or '') else 'a'
                rows.append([f['image_id'], fmt, kind, date, desc if len(desc) < 140 else ''])
            time.sleep(1)
        todo = [(r[0], r[1]) for r in rows if r[0] not in stats_cache]
        with ThreadPoolExecutor(6) as pool:
            for frame_id, st in pool.map(thumb_stats, todo):
                stats_cache[frame_id] = st
        THUMB_CACHE.write_text(json.dumps(stats_cache))
        kept = []
        for r in rows:
            st = stats_cache.get(r[0])
            if is_blank(st):
                continue
            kept.append(r + [min(9, int(st[1] / 7)) if st else 3])
        dropped = len(rows) - len(kept)
        rows = kept
        # A magazine was usually shot over a day or two, so frames too far
        # from a dated photo take the magazine's most common date.
        mag_dates = {}
        for r in rows:
            if r[3]:
                mag_dates.setdefault(frame_key(r[0])[1], Counter())[r[3]] += 1
        for r in rows:
            common = mag_dates.get(frame_key(r[0])[1])
            if not r[3] and common:
                r[3] = common.most_common(1)[0][0]
        rows.sort(key=lambda r: (frame_key(r[0])[2], r[0]))
        (OUT_DIR / f'{mid}.json').write_text(json.dumps({'frames': rows}, separators=(',', ':')))
        print(mid, len(rows), 'kept,', dropped, 'blank dropped', dict(Counter(r[2] for r in rows)), 'dated', sum(1 for r in rows if r[3]), flush=True)


if __name__ == '__main__':
    main()
