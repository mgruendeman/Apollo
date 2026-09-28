#!/usr/bin/env python3
"""A mission time for each photo on a film magazine, so the site can show a
photo with the moment it was taken, not just its day.

    python3 pipeline/photo_times.py 11

Hasselblad frames on a magazine were shot in order. pipeline/photo_anchors.json
pins some of them to a mission time (a frame NASA's caption describes, at the
moment the tape has that activity; each anchor says why), and the frames
between two anchors are spread evenly between their times. Writes
public/photo-index/NN.times.json: {"frames": {frame: GET seconds}, "kinds":
{frame: kind}} (a magazine's kind, where its frames were filed wrongly).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def seconds(get):
    h, m, s = (int(x) for x in get.split(':'))
    return h * 3600 + m * 60 + s


def number(frame):
    return int(re.search(r'-(\d+)[A-Da-d]?$', frame).group(1))   # ("AS11-40-5882a": a second scan of the frame)


def times_for(frames, anchors):
    """{frame: GET} for the magazine's frames, from anchors [(frame number,
    GET)]: frames between two anchors spread evenly (by frame number), and
    frames past the first or last anchor held at it."""
    pts = sorted(anchors)
    out = {}
    for f in frames:
        n = number(f)
        if n <= pts[0][0]:
            out[f] = pts[0][1]
        elif n >= pts[-1][0]:
            out[f] = pts[-1][1]
        else:
            (a, ga), (b, gb) = next((p, q) for p, q in zip(pts, pts[1:]) if p[0] <= n <= q[0])
            out[f] = round(ga + (gb - ga) * (n - a) / (b - a)) if b > a else ga
    return out


def main():
    m = f'{int(sys.argv[1]):02d}'
    spec = json.loads((ROOT / 'pipeline' / 'photo_anchors.json').read_text()).get(str(int(m)), [])
    index = json.loads((ROOT / 'public' / 'photo-index' / f'{m}.json').read_text())['frames']
    times, kinds = {}, {}
    for mag in spec:
        frames = [f[0] for f in index if f[0].startswith(mag['magazine'] + '-')]
        anchors = [(number(a['frame']), seconds(a['get'])) for a in mag['anchors']]
        times.update(times_for(frames, anchors))
        if mag.get('kind'):
            kinds.update({f[0]: mag['kind'] for f in index if f[0] in frames and f[2] != mag['kind']})
    out = ROOT / 'public' / 'photo-index' / f'{m}.times.json'
    out.write_text(json.dumps({'frames': times, 'kinds': kinds}, separators=(',', ':')) + '\n')
    print(f'{len(times)} frames timed, {len(kinds)} refiled: {out}')


if __name__ == '__main__':
    main()
