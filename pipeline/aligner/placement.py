"""Placing tapes on the mission clock and cutting them into pieces of continuous mission time."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np
from .common import tokens, MIN_WORDS

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


def find_start(line_toks, words, lo, hi):
    """Where a line starts among words[lo:hi], for timing it: the first run
    of two or more of its words heard in order (a lone early match, "a" from
    the sentence before, doesn't count), moved back by the line's words
    before that run (about 0.3 s each). Returns (time, share matched)."""
    window = [w[3] for w in words[lo:hi]]
    if not window:
        return None, 0.0
    sm = difflib.SequenceMatcher(None, line_toks, window, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    if not blocks:
        return None, 0.0
    run = next((b for b in blocks if b.size >= 2), blocks[0])
    matched = sum(b.size for b in blocks)
    return words[lo + run.b][0] - 0.3 * run.a, matched / len(line_toks)


def quietest_gap(word_starts, word_ends, a, b):
    """The middle of the longest stretch without speech between tape times
    a and b: where the recorder was most likely stopped and restarted."""
    i = bisect.bisect_left(word_starts, a)
    j = bisect.bisect_right(word_starts, b)
    edges = [a] + [x for k in range(i, j) for x in (word_starts[k], word_ends[k])] + [b]
    gaps = [(edges[k + 1] - edges[k], (edges[k] + edges[k + 1]) / 2) for k in range(0, len(edges) - 1, 2)]
    return max(gaps)[1] if gaps else (a + b) / 2


SPOKEN = re.compile(r"(\d+) hours?,? (\d+) minutes")


def spoken_pieces(words):
    """Rough places on the mission clock for a tape no journal clip placed,
    from the announcer saying the time ("This is Apollo Control at 59 hours,
    9 minutes"): a 40-minute stretch around each time he gives, to search
    for NASA's lines in (which then place the tape exactly). Times he
    mentions that aren't "now" (a burn due at 100 hours 20) are outvoted:
    only times agreeing with another within 3 minutes of offset count."""
    text, at = '', []
    for w in words:
        at.append(len(text))
        text += w[2] + ' '
    found = []
    for mt in SPOKEN.finditer(text):
        i = bisect.bisect_right(at, mt.start()) - 1
        near = text[max(0, mt.start() - 80):mt.end() + 80].lower()
        if 'apollo control' in near:
            found.append((words[i][0], int(mt.group(1)) * 3600 + int(mt.group(2)) * 60))
    good = [(t, g) for t, g in found if sum(abs((g2 - t2) - (g - t)) <= 180 for t2, g2 in found) >= 2]
    return [{'tape_from': max(0.0, t - 1200), 'tape_to': t + 1200, 'get_from': g - (t - max(0.0, t - 1200)), 'rate': 1.0}
            for t, g in good]


def text_pieces(words, grams):
    """Rough places on the mission clock for a tape nothing else placed,
    from what's said on it: every three-word phrase the recogniser heard
    that NASA's transcript has only a few times votes for the tape's offset
    (mission time minus tape time); a stretch of tape whose votes agree
    marks a place. grams: phrase -> [GET of NASA lines holding it].
    Returns 40-minute search stretches, as spoken_pieces does."""
    toks = [(w[0], w[3]) for w in words if w[3]]
    found = []
    step = 60
    for i in range(0, max(0, len(toks) - 3), step):
        votes = {}
        for j in range(i, min(i + 2 * step, len(toks) - 2)):
            hits = grams.get(' '.join(t for _, t in toks[j:j + 3]))
            if hits and len(hits) <= 5:
                for g in hits:
                    key = round((g - toks[j][0]) / 30)
                    votes[key] = votes.get(key, 0) + 1 / len(hits)
        if votes:
            key, score = max(votes.items(), key=lambda kv: kv[1])
            if score >= 4:
                found.append((toks[i][0], toks[i][0] + key * 30))
    return [{'tape_from': max(0.0, t - 1200), 'tape_to': t + 1200, 'get_from': g - (t - max(0.0, t - 1200)), 'rate': 1.0}
            for t, g in found]


def merge_pieces(pieces):
    """Search stretches that overlap on the tape and agree on its offset (within
    30 s) as one, so each line is looked for once, not in every stretch."""
    out = []
    for p in sorted(pieces, key=lambda p: p['tape_from']):
        off = p['get_from'] - p['tape_from']
        if out and p['tape_from'] <= out[-1]['tape_to'] and abs(off - (out[-1]['get_from'] - out[-1]['tape_from'])) <= 30:
            out[-1]['tape_to'] = max(out[-1]['tape_to'], p['tape_to'])
        else:
            out.append(dict(p))
    return out


def pieces_from_anchors(anchors, seconds, word_starts, word_ends):
    """Split a tape's (tape time, GET) anchors into pieces of continuous
    mission time (as place_tapes.segments, with tighter agreement), cut
    at the quietest point between neighbouring pieces."""
    groups = []
    for t, g, *_ in sorted(anchors):
        off = g - t
        if groups and abs(off - groups[-1][-1][1]) <= 8:
            groups[-1].append((t, off))
        else:
            groups.append([(t, off)])
    groups = [grp for grp in groups if len(grp) >= 3]
    # a small group out of line with neighbours that agree with each other
    # is a mismatch (a phrase said twice), not a stretch of the mission
    off = lambda grp: float(np.median([x[1] for x in grp]))
    keep = [grp for i, grp in enumerate(groups)
            if not (0 < i < len(groups) - 1 and len(grp) <= 5 and abs(off(groups[i - 1]) - off(groups[i + 1])) <= 30
                    and abs(off(grp) - off(groups[i - 1])) > 60)]
    groups = keep
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


