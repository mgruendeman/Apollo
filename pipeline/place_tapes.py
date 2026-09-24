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
GOOD = 0.6                   # correlation recorded as a possible match
STRONG = 0.85                # correlation needed to place a tape by it


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


def segments(found, seconds):
    """Split a tape into pieces of continuous mission time.

    Recorders were often stopped through quiet stretches, so one tape holds
    several pieces of the mission. Anchors (journal clips found in the
    tape, in tape order) whose GET - tape-time offsets agree within 20 s
    belong to one piece; a jump in offset starts a new piece. Each piece
    runs from midway between its first anchor and the previous piece's last
    (the exact cut is refined later, when the transcript is timed to the
    tape) to midway to the next piece."""
    pieces = []
    for f in sorted(found, key=lambda f: f['at']):
        off = f['get'] - f['at']
        if pieces and abs(off - pieces[-1]['anchors'][-1][1]) <= 20:
            pieces[-1]['anchors'].append((f['at'], off, f['r'], f['clip']))
        else:
            pieces.append({'anchors': [(f['at'], off, f['r'], f['clip'])]})
    # a lone anchor is trusted only if it matched very strongly
    pieces = [p for p in pieces if len(p['anchors']) >= 2 or p['anchors'][0][2] >= 0.95]
    out = []
    for i, p in enumerate(pieces):
        ats = np.array([x[0] for x in p['anchors']])
        offs = np.array([x[1] for x in p['anchors']])
        rate = 1.0 + (np.polyfit(ats, offs, 1)[0] if len(ats) >= 2 and np.ptp(ats) > 300 else 0.0)   # drift of the tape speed
        lo = 0.0 if i == 0 else (pieces[i - 1]['anchors'][-1][0] + ats[0]) / 2
        hi = seconds if i == len(pieces) - 1 else (ats[-1] + pieces[i + 1]['anchors'][0][0]) / 2
        start_get = float(np.median(offs - (rate - 1.0) * ats)) + lo * rate   # GET at tape time lo
        out.append({'tape_from': round(lo, 1), 'tape_to': round(hi, 1), 'get_from': round(start_get, 1),
                    'rate': round(float(rate), 5), 'anchors': len(ats), 'clips': [x[3] for x in p['anchors']]})
    return out


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
        placement[tape.stem] = {'seconds': round(len(te) / FPS), 'found': found, 'kinds': kinds}
        print(f'[{n}/{len(tapes)}] {tape.stem}: {len(found)} journal clips found', flush=True)

    # A clip found strongly in 3+ tapes is generic sound (tone, static), not a place.
    from collections import Counter
    everywhere = Counter(f['clip'] for e in placement.values() for f in e['found'] if f['r'] >= 0.8)
    covered = 0.0
    for stem, e in placement.items():
        strong = [f for f in e['found'] if f['r'] >= STRONG and everywhere[f['clip']] < 3]
        e['pieces'] = segments(strong, e['seconds'])
        covered += sum(p['tape_to'] - p['tape_from'] for p in e['pieces'])
        where = ', '.join(f"{int(p['get_from']) // 3600:03d}:{int(p['get_from']) % 3600 // 60:02d}" for p in e['pieces'][:6])
        print(f"{stem}: {len(e['pieces'])} pieces {where}{' ...' if len(e['pieces']) > 6 else ''}")
    out = ROOT / 'pipeline' / 'tapes' / f'apollo{m}-placement.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(placement, indent=1))
    print(f'placed {covered / 3600:.1f} h of tape; written to {out}')

if __name__ == '__main__':
    main()
