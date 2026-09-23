"""Add NASA Image Library versions of film frames that are in the scan index.

The film-roll scans (public/photo-index, from scripts/fetch_archive_frames.py)
show the raw film, borders and all. NASA's Image Library has processed,
captioned versions of a subset of those same frames. This searches the
library magazine by magazine and adds every frame it has to
src/data/missionPhotos.json, so the site shows NASA's version (and caption)
instead of the scan. Frames already there are left alone.

A frame's date comes from its caption when the caption names a single day
within the mission, otherwise from the scan index; its kind comes from the
caption, or the scan index when the caption doesn't say.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_nasa_photos import API, DATE_RE, LANDED, MISSIONS, MONTHS, caption, classify  # noqa: E402
from fetch_archive_frames import frame_key  # noqa: E402

ROOT = Path(__file__).parent.parent
OUT = ROOT / 'src' / 'data' / 'missionPhotos.json'
INDEX = ROOT / 'public' / 'photo-index'


def search(query, page):
    url = API + urllib.parse.urlencode({'q': query, 'media_type': 'image', 'page': page})
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))['collection']
        except Exception:
            time.sleep(3 * (attempt + 1))
    return {'items': []}


def main():
    photos = json.loads(OUT.read_text())
    added_total = 0
    for mid, (launch, duration) in sorted(MISSIONS.items()):
        index_path = INDEX / f'{mid}.json'
        if not index_path.exists():
            continue
        frames = {frame_key(f[0]): f for f in json.loads(index_path.read_text())['frames'] if frame_key(f[0])}
        have = {frame_key(p['id']) for p in photos.get(mid, []) if frame_key(p['id'])}
        mags = sorted({k[1] for k in frames})
        found = {}
        for mag in mags:
            for page in range(1, 10):
                coll = search(f'AS{mid}-{mag}', page)
                for item in coll['items']:
                    d = item['data'][0]
                    k = frame_key(d['nasa_id'])
                    if not k or k not in frames or k in have:
                        continue
                    # Prefer the plain "as11-40-5875" id over a "KSC-" copy.
                    if k in found and not found[k][0].lower().startswith('ksc-'):
                        continue
                    found[k] = (d['nasa_id'], d.get('description', '') or '')
                if not any(link.get('rel') == 'next' for link in coll.get('links', [])):
                    break
                time.sleep(0.3)
        first_day = launch.date().isoformat()
        last_day = (launch + timedelta(seconds=duration)).date().isoformat()
        added = []
        for k, (nid, desc) in sorted(found.items()):
            row = frames[k]
            cap = caption(desc) if desc else ''
            kind = classify(cap, desc, landed=mid in LANDED, earth_orbit_only=mid == '09') if cap else 'other'
            if kind == 'other':
                kind = row[2]
            date = row[3]
            m = DATE_RE.search(desc)
            if m and not m.group(2) and m.group(3)[:3].lower() in MONTHS:
                day = f'{int(m.group(4)):04d}-{MONTHS[m.group(3)[:3].lower()]:02d}-{int(m.group(1)):02d}'
                if first_day <= day <= last_day:
                    date = day
            added.append({'id': nid, 'date': date, 'kind': kind, 'caption': cap or row[4] or ''})
        photos.setdefault(mid, []).extend(added)
        photos[mid].sort(key=lambda p: (p['date'] or '9999', p['id'].lower()))
        added_total += len(added)
        print(mid, 'magazines', len(mags), 'added', len(added), flush=True)
    OUT.write_text(json.dumps(photos, indent=1, ensure_ascii=False) + '\n')
    print('total added', added_total)


if __name__ == '__main__':
    main()
