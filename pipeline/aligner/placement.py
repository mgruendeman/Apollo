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


def _find_unique(line_toks, words, lo, hi):
    """Where a line is among words[lo:hi], only if one place clearly beats
    every other more than 20 s away (a readback repeats the words it reads
    back). Returns (tape time, share of the line's words matched) or (None, 0)."""
    n = len(line_toks)
    scores = []
    for a in range(lo, max(lo + 1, hi - n // 2), 2):
        window = [w[3] for w in words[a:min(hi, a + n + 6)]]
        if not window:
            break
        sm = difflib.SequenceMatcher(None, line_toks, window, autojunk=False)
        blocks = [b for b in sm.get_matching_blocks() if b.size]
        if blocks:
            # where the line starts: its first run of two or more words heard,
            # less the line's words before that run (a scan-damaged opening)
            run = next((b for b in blocks if b.size >= 2), blocks[0])
            last = a + blocks[-1].b + blocks[-1].size - 1
            scores.append((sum(b.size for b in blocks), a + run.b, run.a, a + blocks[0].b, last))
    if not scores:
        return None, 0.0
    best, at, before, first, last = max(scores)
    # a rival: as good a match whose words are all clear of the best one's
    rival = max((m for m, _, _, f, e in scores
                 if words[e][0] < words[first][0] - 20 or words[f][0] > words[last][0] + 20), default=0)
    if rival >= best - 2:
        return None, 0.0
    return words[at][0] - 0.3 * before, best / n


def _in_order(found):
    """The anchors (in NASA's line order) whose tape times also run in order:
    the longest such run. A stock phrase ("Houston. Roger. Out.") found at
    the wrong place on the tape breaks the order, so can't bound a search."""
    tails, prev, at = [], [None] * len(found), []
    for i, a in enumerate(found):
        j = bisect.bisect_left([found[k][0] for k in at], a[0])
        if j == len(at):
            at.append(i)
        else:
            at[j] = i
        prev[i] = at[j - 1] if j else None
    out, i = [], at[-1] if at else None
    while i is not None:
        out.append(found[i])
        i = prev[i]
    return out[::-1]


def chain_anchors(rows, anchors, words, starts, g_lo, g_hi):
    """A second look for NASA's lines the first missed, between the lines it
    found. Words on a tape come in the order they were said, so a line
    printed between two found lines is on the tape between them, however
    far from where a steady offset would put it: where the recorder ran in
    bursts (stopped through the quiet, started by a voice) mission time
    outruns the tape, minutes over a quarter of an hour. Only clear, single
    matches count. anchors: [(tape time, GET, row index)]; returns more."""
    found = _in_order(sorted({a[2]: a for a in anchors}.values(), key=lambda a: a[2]))
    idx = [a[2] for a in found]
    extra, prev_t = [], None
    for k, r in enumerate(rows):
        j = bisect.bisect_left(idx, k)
        if j < len(idx) and idx[j] == k:
            prev_t = found[j][0]
            continue
        if r['getApprox'] or not g_lo <= r['getSeconds'] <= g_hi or prev_t is None or j >= len(found):
            continue
        toks = tokens(r['text'])
        next_t = found[j][0]
        if len(toks) < 6 or not prev_t < next_t <= prev_t + 1200:
            continue
        lo, hi = bisect.bisect_left(starts, prev_t), bisect.bisect_right(starts, next_t)
        t, share = _find_unique(toks, words, lo, hi)
        if t is not None and share >= 0.75:
            extra.append((t, r['getSeconds'], k))
            prev_t = t
    return extra


def pieces_from_anchors(anchors, seconds, word_starts, word_ends, sure=()):
    """Split a tape's (tape time, GET) anchors into pieces of continuous
    mission time (as place_tapes.segments, with tighter agreement), cut
    at the quietest point between neighbouring pieces. A piece needs three
    anchors agreeing, or one of the `sure` ones (a line found between two
    others, in one clear place: chain_anchors), where the recorder ran in
    bursts of a line or two."""
    sure = {(t, g) for t, g, *_ in sure}
    groups = []
    for t, g, *_ in sorted(anchors):
        off = g - t
        if groups and abs(off - groups[-1][-1][1]) <= 8:
            groups[-1].append((t, off))
        else:
            groups.append([(t, off)])
    # A small group stands as a piece only if it holds a sure anchor and jumps
    # further from the groups either side than the line timing can absorb
    # (sync_to_tape looks 30 s back): a burst on a recorder that ran in
    # bursts. A line anchored a little off mustn't cut a steady stretch.
    med = lambda grp: float(np.median([x[1] for x in grp]))
    # First, before any group is dropped: a small group built on the second
    # look's anchors, out of line with the groups either side, which agree
    # with each other, is a mismatch or a misprinted time ("51:09:41" for
    # 51:12:41), not a stretch of the mission. (Groups of the first look's
    # anchors alone keep the older, looser test below: where NASA's lines are
    # sparse, as on the moonwalks, a real half hour of tape can rest on three.)
    has_sure = lambda grp: any((t, t + off) in sure for t, off in grp)
    groups = [grp for i, grp in enumerate(groups)
              if not (0 < i < len(groups) - 1 and len(grp) <= 5 and has_sure(grp)
                      and abs(med(groups[i - 1]) - med(groups[i + 1])) <= 30 and abs(med(grp) - med(groups[i - 1])) > 30)]
    merged = groups   # (small groups aren't merged: noise at one offset would pass for a stretch)
    big = [i for i, grp in enumerate(merged) if len(grp) >= 3]
    keep = []
    for i, grp in enumerate(merged):
        if len(grp) >= 3:
            keep.append(grp)
            continue
        if not has_sure(grp):
            continue
        before = [j for j in big if j < i]
        after = [j for j in big if j > i]
        near = ([merged[before[-1]]] if before else []) + ([merged[after[0]]] if after else [])
        if all(abs(med(grp) - med(n)) > 30 for n in near):
            keep.append(grp)
    groups = keep
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


