"""Place NASA's tapes on the mission clock, using the journal's clips.

The Apollo Flight/Surface Journal clips were cut from NASA's recordings and
each has a known mission time (GET). This finds every journal clip inside
every tape by matching their loudness patterns (as journal_baseline.py
does), then fits each tape's mission time from the matches:

    GET = start_get + rate * (seconds into the tape)

rate is 1 for a tape at the right speed; a tape recorded slow or fast shows
a different rate. It also records which kind of journal clip each tape
matched: air-to-ground, the public-affairs broadcast ("pao"), or onboard
("ob"), which says what the tape holds.

    python pipeline/place_tapes.py 11 --media /media/mark/T7/apollo-media

Writes pipeline/tapes/apollo<NN>-placement.json. Needs: ffmpeg, curl, numpy.
"""
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
SR, HOP = 4000, 400          # loudness envelope at 10 frames a second
FPS = SR / HOP
MIN_CLIP_S = 20              # shorter clips match too loosely to trust
GOOD = 0.6                   # correlation needed to count as found


def envelope(path, cache):
    """Normalised log-loudness, 10 frames a second, cached as .npy."""
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return np.load(cache)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    frames = a[: len(a) // HOP * HOP].reshape(-1, HOP)
    e = np.log1p(np.sqrt((frames ** 2).mean(1)) * 1000).astype(np.float32)
    e = (e - e.mean()) / (e.std() + 1e-9)
    np.save(cache, e)
    return e


def match(tape, clip):
    """Best (frame offset, correlation) of clip inside tape, normalised per window."""
    n = len(clip)
    if len(tape) < n or n < 2:
        return None, 0.0
    size = 1 << int(np.ceil(np.log2(len(tape) + n)))
    corr = np.fft.irfft(np.fft.rfft(tape, size) * np.conj(np.fft.rfft(clip - clip.mean(), size)), size)[: len(tape) - n + 1]
    cs = np.cumsum(np.r_[0, tape], dtype=np.float64)
    cs2 = np.cumsum(np.r_[0, tape.astype(np.float64) ** 2])
    mean = (cs[n:] - cs[:-n]) / n
    std = np.sqrt(np.maximum((cs2[n:] - cs2[:-n]) / n - mean ** 2, 1e-9))
    r = corr / (n * std * (clip.std() + 1e-9))
    i = int(np.argmax(r))
    return i, float(r[i])


def kind(clip_id):
    c = clip_id.lower()
    return 'broadcast' if 'pao' in c else 'onboard' if c.endswith('ob') or 'ob.' in c or '_ob' in c else 'air-to-ground'


def fit(points):
    """GET = start + rate * t from (t, GET, r) points: the largest set that
    agrees within 10 s of a line, least-squares."""
    pts = np.array(points, dtype=float)
    best = None
    for i in range(len(pts)):
        for j in range(i, len(pts)):
            if j == i:
                rate = 1.0
            elif abs(pts[j, 0] - pts[i, 0]) > 60:
                rate = (pts[j, 1] - pts[i, 1]) / (pts[j, 0] - pts[i, 0])
                if not 0.4 < rate < 2.5:
                    continue
            else:
                continue
            start = pts[i, 1] - rate * pts[i, 0]
            ok = np.abs(pts[:, 1] - (start + rate * pts[:, 0])) <= 10
            if best is None or ok.sum() > best.sum():
                best = ok
    sel = pts[best]
    if len(sel) >= 2 and np.ptp(sel[:, 0]) > 60:
        rate, start = np.polyfit(sel[:, 0], sel[:, 1], 1)
    else:
        rate, start = 1.0, float(np.median(sel[:, 1] - sel[:, 0]))
    return float(start), float(rate), int(len(sel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    media = Path(args.media).expanduser()
    clips = [c for c in json.loads((ROOT / 'src' / 'data' / 'clips' / f'apollo{m}.json').read_text())
             if c.get('durationSeconds', 0) >= MIN_CLIP_S]
    jdir = media / 'journal' / m

    def fetch(c):
        dest = jdir / (c['id'] + '.mp3')
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['curl', '-sSfL', '--retry', '3', '-o', str(dest), c['audioUrl']], check=False)
        return c, dest

    with ThreadPoolExecutor(6) as pool:
        fetched = [(c, d) for c, d in pool.map(fetch, clips) if d.exists() and d.stat().st_size > 0]
    print(f'{len(fetched)} journal clips of {MIN_CLIP_S}+ s', flush=True)
    cenv = [(c, envelope(d, media / 'envelopes' / 'journal' / m / (c['id'] + '.npy'))) for c, d in fetched]

    # only fully downloaded tapes (a partial file would cache a partial envelope)
    sizes = {Path(f['name']).name: f['bytes'] for f in json.loads((ROOT / 'pipeline' / 'nasa_audio_inventory.json').read_text())[m]['files']}
    tapes = sorted(t for t in (media / 'audio-orig' / m).glob('*.mp3') if t.stat().st_size == sizes.get(t.name))
    placement = {}
    for n, tape in enumerate(tapes, 1):
        te = envelope(tape, media / 'envelopes' / 'tapes' / m / (tape.stem + '.npy'))
        points, kinds, found = [], {}, []
        for c, ce in cenv:
            i, r = match(te, ce)
            if i is not None and r >= GOOD:
                points.append((i / FPS, c['getSeconds'], r))
                kinds[kind(c['id'])] = kinds.get(kind(c['id']), 0) + 1
                found.append({'clip': c['id'], 'at': round(i / FPS, 1), 'get': c['getSeconds'], 'r': round(r, 2)})
        entry = {'seconds': round(len(te) / FPS), 'matches': len(points), 'kinds': kinds, 'found': found}
        if points:
            start, rate, agree = fit(points)
            entry.update({'start_get': round(start, 1), 'rate': round(rate, 4), 'agreeing': agree})
        placement[tape.stem] = entry
        out = ROOT / 'pipeline' / 'tapes' / f'apollo{m}-placement.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(placement, indent=1))
        if 'start_get' in entry:
            s = int(entry['start_get'])
            print(f"[{n}/{len(tapes)}] {tape.stem}: GET {s // 3600:03d}:{s % 3600 // 60:02d}:{s % 60:02d}, rate {entry['rate']}, "
                  f"{entry['agreeing']}/{len(points)} matches agree, {kinds}", flush=True)
        else:
            print(f'[{n}/{len(tapes)}] {tape.stem}: no journal clip found in it', flush=True)


if __name__ == '__main__':
    main()
