"""The transcript around a moment, next to what the tape says there.

    python3 pipeline/look_transcript.py 11 5:45:27 [--before 40] [--after 60] [--media $M]

Prints the timeline's lines (flags: a = time lost in the scan, n = not on
the recording, o = talked over; PAO = the announcer), then the words the
speech recogniser heard on the tape over the same stretch, grouped by
pauses, with their mission times. For checking listeners' reports: which
words are really said, by whom, and when.
"""
import argparse
import bisect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def seconds(t):
    parts = [float(p) for p in t.split(':')]
    return sum(p * 60 ** k for k, p in enumerate(reversed(parts)))


def fmt(g):
    return f"{int(g) // 3600:03d}:{int(g) % 3600 // 60:02d}:{int(g) % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('get', help='mission time, as seconds or h:mm:ss')
    ap.add_argument('--before', type=float, default=40)
    ap.add_argument('--after', type=float, default=60)
    ap.add_argument('--media', default='/media/mark/T7/apollo-media')
    a = ap.parse_args()
    g0 = seconds(a.get)
    tl = json.loads((ROOT / 'public' / 'timeline' / f'apollo{a.mission}.json').read_text())
    for i, l in enumerate(tl['lines']):
        if g0 - a.before <= l['g'] <= g0 + a.after:
            flags = ''.join(k for k in ('a', 'n', 'o') if l.get(k))
            print(f"  [{i}] {fmt(l['g'])} {l['s']}{' (' + flags + ')' if flags else ''}{' PAO' if l.get('c') else ''}: {l['t']}")
    segs = tl['segments']
    k = bisect.bisect_right([s['get'] for s in segs], g0) - 1
    if k < 0:
        return
    s = segs[k]
    asr = Path(a.media) / 'asr' / a.mission / f"{s['tape']}.json"
    if s.get('journal') or not asr.exists():
        print('  (no tape here)')
        return
    t0 = s['from'] + (g0 - s['get']) / s['rate']
    print(f"  --- tape {s['tape']}, {t0:.0f} s in:")
    line, last = [], None
    for w in json.loads(asr.read_text()):
        if not t0 - a.before <= w[0] <= t0 + a.after:
            continue
        if last is not None and w[0] - last > 1.5:
            print('    ' + ' '.join(line))
            line = []
        if not line:
            line.append(f"[{fmt(s['get'] + (w[0] - s['from']) * s['rate'])}]")
        line.append(w[2].strip())
        last = w[1]
    if line:
        print('    ' + ' '.join(line))


if __name__ == '__main__':
    main()
