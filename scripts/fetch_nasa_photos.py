"""Build src/data/missionPhotos.json from the NASA Image and Video Library.

For each mission, collects NASA public-domain photos whose NASA caption
dates them inside the flight (launch day through splashdown day), keeps
NASA's own caption, and sorts each one into a rough kind (launch, earth,
lunar-orbit, surface, interior, mission-control, recovery) from that
caption, so the app can show photos from the right day and phase. Images
are served from NASA's images-assets.nasa.gov, not copied into the repo.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / 'src' / 'data' / 'missionPhotos.json'
API = 'https://images-api.nasa.gov/search?'
LANDED = {'11', '12', '14', '15', '16', '17'}

missions_js = (ROOT / 'src' / 'data' / 'missions.js').read_text()
MISSIONS = {}
for m in re.finditer(r"id: '(\d\d)',.*?launchUtc: '([^']+)',\s*durationSeconds: (\d+)", missions_js, re.S):
    MISSIONS[m.group(1)] = (datetime.fromisoformat(m.group(2).replace('Z', '+00:00')), int(m.group(3)))

MONTHS = {m: i for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
DATE_RE = re.compile(r'\((\d{1,2})(?:\s*[-\u2013]\s*(\d{1,2}))?\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})\)')

KINDS = [
    ('recovery', r'recovery|splashdown|splashed|hornet|iwo jima|yorktown|ticonderoga|okinawa|new orleans|guadalcanal|princeton|quarantine facility|aboard the u\.?s\.?s'),
    ('mission-control', r'mission control|operations control room|\bmocr\b|flight director|console'),
    ('launch', r'launched from|liftoff|lift-off|lifts off|is launched|launch of|pad a|pad b|launch complex'),
    ('surface', r'lunar surface|extravehicular|\beva\b|moonwalk|lunar roving|landing site|boulder|traverse|station \d|alsep|footprint|bootprint|flag'),
    ('lunar-orbit', r'lunar orbit|from the (command|lunar) module|far ?side|farside|orbiting the moon|crater .* (from orbit|photographed from)|lunar module in|earthrise|lunar horizon|moon.s horizon|approach(ing)? the moon|trans-?earth'),
    ('earth', r'\bearth\b|nautical miles|africa|ocean|continent|cloud'),
    ('interior', r'inside|interior|cabin|onboard|on board|television transmission|tv transmission'),
]


def caption(desc):
    text = desc.split('---', 1)[-1] if '---' in desc else desc
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.split(r'(?:Photo credit|Image credit|Editor.s note)', text, flags=re.I)[0].strip()
    first = re.match(r'(.{40,260}?[.!?])(\s|$)', text)
    return (first.group(1) if first else text[:260]).strip()


def classify(first_sentence, desc, landed, earth_orbit_only):
    # NASA's captions often end with boilerplate ("...remained with the CSM
    # in lunar orbit"), so judge by the opening sentence first.
    kind = 'other'
    for text in (first_sentence.lower(), desc.lower()):
        kind = next((k for k, pattern in KINDS if re.search(pattern, text)), 'other')
        if kind != 'other':
            break
    if earth_orbit_only and kind in ('surface', 'lunar-orbit'):
        kind = 'earth'
    elif not landed and kind == 'surface':
        kind = 'lunar-orbit'
    return kind


def search(query, page):
    url = API + urllib.parse.urlencode({'q': query, 'media_type': 'image', 'page': page})
    return json.load(urllib.request.urlopen(url, timeout=60))['collection']


def main():
    out = {}
    for mid, (launch, duration) in sorted(MISSIONS.items()):
        first_day = launch.date()
        last_day = (launch + timedelta(seconds=duration)).date()
        n = int(mid)
        seen, photos = set(), []
        queries = [f'AS{mid}', f'Apollo {n}', f'Apollo {n} lunar surface', f'Apollo {n} extravehicular activity',
                   f'Apollo {n} lunar orbit', f'Apollo {n} Earth', f'Apollo {n} launch', f'Apollo {n} recovery',
                   f'Apollo {n} Mission Control', f'Apollo {n} spacecraft', f'Apollo {n} astronaut', f'Apollo {n} crew',
                   f'Apollo {n} television', f'Apollo {n} moon', f'Apollo {n} splashdown', f'Apollo {n} lunar module']
        for query in queries:
            for page in range(1, 40):
                try:
                    coll = search(query, page)
                except Exception:
                    break
                for item in coll['items']:
                    d = item['data'][0]
                    nid, desc = d['nasa_id'], d.get('description', '') or ''
                    if nid.lower() in seen:
                        continue
                    if not re.search(rf'apollo {n}\b|\bas{mid}-', desc + ' ' + d.get('title', ''), re.I):
                        continue
                    m = DATE_RE.search(desc)
                    if not m or m.group(3)[:3].lower() not in MONTHS:
                        continue
                    year, month = int(m.group(4)), MONTHS[m.group(3)[:3].lower()]
                    day = datetime(year, month, int(m.group(1)), tzinfo=timezone.utc).date()
                    end = datetime(year, month, int(m.group(2)), tzinfo=timezone.utc).date() if m.group(2) else day
                    if not (first_day <= day <= last_day and first_day <= end <= last_day):
                        continue
                    seen.add(nid.lower())
                    cap = caption(desc)
                    kind = classify(cap, desc, landed=mid in LANDED, earth_orbit_only=mid == '09')
                    # A caption dated with a range ("16-24 July") covers a whole
                    # film roll, so the photo's own day isn't known.
                    photos.append({'id': nid, 'date': day.isoformat() if end == day else None,
                                   'kind': kind, 'caption': cap})
                if not coll.get('links') or not any(l.get('rel') == 'next' for l in coll['links']):
                    break
        photos.sort(key=lambda p: (p['date'] or '9999', p['id'].lower()))
        out[mid] = photos
        kinds = {}
        for p in photos:
            kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
        print(mid, len(photos), kinds, flush=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
