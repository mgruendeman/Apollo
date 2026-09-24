"""Time NASA's transcript to NASA's tapes, and build the mission's timeline.

Inputs, per mission:
  pipeline/tapes/apolloNN-placement.json   tape pieces placed from journal
                                           clips (place_tapes.py)
  <media>/asr/NN/<tape>.json               every recognised word with its
                                           time on the tape (transcribe_tapes.py)
  data/nasa-transcripts/asNN-tec.json      NASA's air-to-ground transcript
  public/transcripts/apolloNN.json         the journal transcript, used only
                                           to put names to NASA's speaker codes

For every NASA line in a placed piece it looks for the line's words among
the recognised words near where the piece puts it, and takes the time of
the match. Those anchors re-fit each tape's pieces exactly (the recorders
were stopped through quiet stretches, so a tape is several pieces of
mission time). Output, public/timeline/apolloNN.json:

  segments: [{tape, from, to, get, rate}]   tape seconds from..to play
                                            mission time get + rate*(t - from)
  lines:    [{g, s, t}]                     NASA's lines by mission time
                                            (seconds), speaker name, text

    python pipeline/align_tapes.py 11 --media /media/mark/T7/apollo-media
"""
import argparse
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
TOKEN = re.compile(r"[a-z0-9]+")
CREW = {'11': {'CDR': 'Armstrong', 'CMP': 'Collins', 'LMP': 'Aldrin'}}
OTHER = {'CT': 'Comm Tech', 'SC': 'Spacecraft', 'MS': 'Mission Control', 'HORNET': 'USS Hornet',
         'SWIM': 'Swimmer', 'MSFN': 'Tracking station', 'PAO': 'Mission Control', 'IWO': 'Recovery'}
SEARCH_S = 90          # how far from the piece's prediction to look for a line
MIN_WORDS = 3


def tokens(text):
    return TOKEN.findall(text.lower().replace("'", ''))


def get_seconds(get):
    h, m, s = (int(x) for x in get.split(':'))
    return h * 3600 + m * 60 + s


def speaker_names(mission, rows):
    """Names for NASA's codes: crew by position; for CC (the capsule
    communicator) the journal's name for whoever was on shift at that time."""
    journal = json.loads((ROOT / 'public' / 'transcripts' / f'apollo{mission}.json').read_text())
    crew = CREW.get(mission, {})
    crew_names = set(crew.values())
    capcoms = sorted((get_seconds(l['get']), l['speaker']) for lines in journal.values() for l in lines
                     if l.get('channel', 'air-to-ground') == 'air-to-ground' and l['speaker'] not in crew_names
                     and l['speaker'] not in ('Mission Control', 'PAO'))
    times = [t for t, _ in capcoms]

    def name(row):
        code = row['speaker']
        if code in crew:
            return crew[code]
        if code == 'CC' and capcoms:
            i = min(max(bisect.bisect_left(times, row['getSeconds']), 0), len(times) - 1)
            near = [capcoms[j] for j in (i - 1, i) if 0 <= j < len(capcoms)]
            return min(near, key=lambda c: abs(c[0] - row['getSeconds']))[1]
        return OTHER.get(code, 'Unknown' if code == '?' else code)
    return name


def find(line_toks, words, lo, hi):
    """Best place for a line's words among words[lo:hi]: (tape time, share
    of the line's words matched in order)."""
    window = [w[3] for w in words[lo:hi]]
    if not window:
        return None, 0.0
    sm = difflib.SequenceMatcher(None, line_toks, window, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    if not blocks:
        return None, 0.0
    matched = sum(b.size for b in blocks)
    first = blocks[0]
    return words[lo + first.b][0], matched / len(line_toks)


def quietest_gap(word_starts, word_ends, a, b):
    """The middle of the longest stretch without speech between tape times
    a and b: where the recorder was most likely stopped and restarted."""
    i = bisect.bisect_left(word_starts, a)
    j = bisect.bisect_right(word_starts, b)
    edges = [a] + [x for k in range(i, j) for x in (word_starts[k], word_ends[k])] + [b]
    gaps = [(edges[k + 1] - edges[k], (edges[k] + edges[k + 1]) / 2) for k in range(0, len(edges) - 1, 2)]
    return max(gaps)[1] if gaps else (a + b) / 2


def pieces_from_anchors(anchors, seconds, word_starts, word_ends):
    """Split a tape's (tape time, GET) anchors into pieces of continuous
    mission time (as place_tapes.segments, with tighter agreement), cut
    at the quietest point between neighbouring pieces."""
    groups = []
    for t, g in sorted(anchors):
        off = g - t
        if groups and abs(off - groups[-1][-1][1]) <= 8:
            groups[-1].append((t, off))
        else:
            groups.append([(t, off)])
    groups = [grp for grp in groups if len(grp) >= 3]
    out = []
    for i, grp in enumerate(groups):
        ts = np.array([x[0] for x in grp])
        offs = np.array([x[1] for x in grp])
        slope = np.polyfit(ts, offs, 1)[0] if np.ptp(ts) > 300 else 0.0
        c = float(np.median(offs - slope * ts))
        lo = 0.0 if i == 0 else quietest_gap(word_starts, word_ends, groups[i - 1][-1][0], ts[0])
        hi = seconds if i == len(groups) - 1 else quietest_gap(word_starts, word_ends, ts[-1], groups[i + 1][0][0])
        out.append({'from': round(lo, 2), 'to': round(hi, 2), 'get': round(c + (1 + slope) * lo, 2),
                    'rate': round(1 + float(slope), 6), 'anchors': len(grp)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    media = Path(args.media).expanduser()
    placement = json.loads((ROOT / 'pipeline' / 'tapes' / f'apollo{m}-placement.json').read_text())
    rows = [r for r in json.loads((ROOT / 'data' / 'nasa-transcripts' / f'as{m}-tec.json').read_text())
            if r['getSeconds'] > 0 or r['speaker'] not in ('MS', '?')]
    name = speaker_names(m, rows)

    segments, stats = [], {'anchored': 0, 'tried': 0}
    for tape, entry in sorted(placement.items()):
        asr = media / 'asr' / m / f'{tape}.json'
        if not entry.get('pieces') or not asr.exists():
            continue
        words = [(w[0], w[1], w[2], (tokens(w[2]) or [''])[0]) for w in json.loads(asr.read_text())]
        starts = [w[0] for w in words]
        anchors = []
        for piece in entry['pieces']:
            g0, g1 = piece['get_from'], piece['get_from'] + (piece['tape_to'] - piece['tape_from']) * piece['rate']
            for r in rows:
                if not g0 - 60 <= r['getSeconds'] <= g1 + 60 or r['getApprox']:
                    continue
                toks = tokens(r['text'])
                if len(toks) < MIN_WORDS:
                    continue
                stats['tried'] += 1
                t_pred = piece['tape_from'] + (r['getSeconds'] - piece['get_from']) / piece['rate']
                lo = bisect.bisect_left(starts, t_pred - SEARCH_S)
                hi = bisect.bisect_right(starts, t_pred + SEARCH_S)
                t, share = find(toks, words, lo, hi)
                if t is not None and share >= 0.6:
                    anchors.append((t, r['getSeconds']))
                    stats['anchored'] += 1
        for p in pieces_from_anchors(anchors, entry['seconds'], starts, [w[1] for w in words]):
            segments.append({'tape': tape, **p})

    segments.sort(key=lambda s: s['get'])
    lines = [{'g': r['getSeconds'], 's': name(r), 't': r['text']} for r in rows]
    out = ROOT / 'public' / 'timeline' / f'apollo{m}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'mission': m, 'segments': segments, 'lines': lines}, separators=(',', ':')))
    covered = sum((s['to'] - s['from']) * s['rate'] for s in segments) / 3600
    print(f"{stats['anchored']} of {stats['tried']} lines found on the tapes; {len(segments)} segments covering {covered:.1f} h; "
          f"{len(lines)} lines; written to {out}")


if __name__ == '__main__':
    main()
