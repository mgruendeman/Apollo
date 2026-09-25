"""Timing NASA's lines to where they are heard on the tapes; rebuilding garbled lines; marking unheard ones."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np
from .common import tokens, MIN_WORDS
from .placement import find, find_start
from .ocr_repair import _suspect, _core
from .announcer import LABELS

def sync_to_tape(lines, segments, tape_words):
    """Each line starts where its words are heard on the tape, not at NASA's
    printed second (which can be several seconds out, typed from the
    tapes by ear): the transcript highlights with the voice.

    Lines are found in order along each stretch of tape: each is searched
    for after where the one before it was found, and within a minute of its
    printed time, so a readback ("A CMC self-check on page F-22-2...") is
    found in the reply, not in the instruction it repeats. Returns how many
    lines moved."""
    end = lambda sg: sg['get'] + (sg['to'] - sg['from']) * sg['rate']
    gets = [sg['get'] for sg in segments]
    groups = {}
    for i, l in enumerate(lines):
        if l.get('a') or l.get('c'):
            continue
        k = bisect.bisect_right(gets, l['g']) - 1
        if k >= 0 and l['g'] <= end(segments[k]) + 30 and segments[k]['tape'] in tape_words and not segments[k].get('journal'):
            groups.setdefault(k, []).append(i)
    n = 0
    for k, idx in groups.items():
        sg = segments[k]
        words, starts = tape_words[sg['tape']]
        lo_i, hi_i = bisect.bisect_left(starts, sg['from']), bisect.bisect_right(starts, sg['to'])
        heard = [(sg['get'] + (w[0] - sg['from']) * sg['rate'],) + tuple(w[1:]) for w in words[lo_i:hi_i]]
        at = [h[0] for h in heard]
        cursor = 0
        for i in sorted(idx, key=lambda i: lines[i]['g']):
            toks = tokens(lines[i]['t'])
            if len(toks) < MIN_WORDS:
                continue
            lo = max(cursor, bisect.bisect_left(at, lines[i]['g'] - 30))
            hi = bisect.bisect_right(at, lines[i]['g'] + 60)
            if lo >= hi:
                continue
            g, share = find_start(toks, heard, lo, hi)
            if g is None or share < 0.6:
                continue
            j = bisect.bisect_left(at, g)
            cursor = j + max(1, int(0.7 * len(toks)))
            if abs(g - lines[i]['g']) >= 0.5:
                lines[i]['g'] = round(g, 1)
                n += 1
    return n


def time_untimed(lines, segments, tape_words):
    """Times for NASA's lines whose time the scan lost (or, on the
    moonwalks, printed as the day and hour only), from the tapes: between
    the timed lines either side, each is looked for in order among the words
    heard on the tape over that stretch. Returns how many were timed."""
    end = lambda sg: sg['get'] + (sg['to'] - sg['from']) * sg['rate']
    done = 0
    timed = [i for i, l in enumerate(lines) if not l.get('a')]
    for p, n in zip([-1] + timed, timed + [len(lines)]):
        run = range(p + 1, n)
        if not run:
            continue
        g0 = lines[p]['g'] if p >= 0 else -3600
        g1 = lines[n]['g'] if n < len(lines) else g0 + 3600
        g1 = max(g1, g0 + 60)
        # the tape words over [g0, g1], in mission order, with their mission times
        heard = []
        for sg in segments:
            if end(sg) < g0 or sg['get'] > g1 or sg['tape'] not in tape_words or sg.get('journal'):
                continue
            words, starts = tape_words[sg['tape']]
            ta = sg['from'] + (max(g0, sg['get']) - sg['get']) / sg['rate']
            tb = sg['from'] + (min(g1, end(sg)) - sg['get']) / sg['rate']
            for w in words[bisect.bisect_left(starts, ta):bisect.bisect_right(starts, tb)]:
                heard.append((sg['get'] + (w[0] - sg['from']) * sg['rate'],) + tuple(w[1:]))
        heard.sort()
        heard_at = [h[0] for h in heard]
        cursor = 0
        for i in run:
            toks = tokens(lines[i]['t'])
            if len(toks) < MIN_WORDS or cursor >= len(heard):
                continue
            g, share = find_start(toks, heard, cursor, min(len(heard), cursor + 400 + 3 * len(toks)))
            if g is not None and share >= 0.6:
                lines[i]['g'] = round(g)
                lines[i].pop('a', None)
                cursor = bisect.bisect_right(heard_at, g)
                done += 1
    # still-untimed lines keep their place between their neighbours
    for i in range(1, len(lines)):
        if lines[i].get('a') and lines[i]['g'] < lines[i - 1]['g']:
            lines[i]['g'] = lines[i - 1]['g']
    return done


def rebuild_from_tape(lines, segments, tape_words, vocab):
    """Lines the scan left mostly garbled, written again from the tape.

    Where a third or more of a NASA line's words are still damaged after
    repair, and the tape at that moment holds about as many words, which
    agree with the NASA words that did survive, the line's text becomes the
    words heard on the tape, marked 'r' (from the recording). Returns the
    count."""
    gets = [sg['get'] for sg in segments]
    crew = [l for l in lines if not l.get('c') and not l.get('a')]
    n = 0
    for idx, l in enumerate(crew):
        words = l['t'].split()
        bad = [w for w in words if _suspect(_core(w)[1], vocab)]
        if len(words) < 3 or len(bad) < 2 or len(bad) < len(words) / 3:
            continue
        k = bisect.bisect_right(gets, l['g']) - 1
        if k < 0:
            continue
        sg = segments[k]
        if sg['tape'] not in tape_words or sg.get('journal'):
            continue
        t0 = sg['from'] + (l['g'] - sg['get']) / sg['rate']
        nxt = crew[idx + 1]['g'] if idx + 1 < len(crew) else l['g'] + 60
        t1 = min(sg['to'], sg['from'] + (nxt - sg['get']) / sg['rate'], t0 + 6 + 0.6 * len(words))
        if not sg['from'] <= t0 < sg['to'] or t1 <= t0:
            continue
        tw, starts = tape_words[sg['tape']]
        heard = [w for w in tw[bisect.bisect_left(starts, t0 - 1.5):bisect.bisect_left(starts, t1 - 0.2)]
                 if re.sub(r"[^a-z]", '', w[2].lower()) not in LABELS]
        if not (0.6 * len(words) <= len(heard) <= 1.8 * len(words) + 2):
            continue
        kept = [_core(w)[1].lower() for w in words if w not in bad]
        said = [re.sub(r"[^a-z0-9']", '', w[2].lower()) for w in heard]
        if difflib.SequenceMatcher(None, kept, said, autojunk=False).ratio() < 0.45:
            continue
        text = ' '.join(w[2] for w in heard).strip()
        l['t'], l['r'] = text[:1].upper() + text[1:], 1
        n += 1
    return n


def mark_unheard(lines, segments, tape_words, envelopes):
    """NASA's lines that fall where the tape is silent: NASA transcribed the
    full air-to-ground loop, and these tapes are the broadcast copy, which
    sometimes missed a call. Marked 'n' (not on this recording).

    Silent means both: the recogniser heard no words there, and the tape's
    loudness is flat (the recogniser misses faint speech a listener can
    still make out). envelopes: folder of place_tapes' loudness envelopes
    (10 a second, normalised). Silence on these tapes varies by about 0.1;
    faint speech can vary by as little as 0.3."""
    import numpy as np
    loud = {}

    def flat(tape, a, b):
        if tape not in loud:
            f = envelopes / f'{tape}.npy'
            loud[tape] = np.load(f) if f.exists() else None
        e = loud[tape]
        if e is None:
            return False
        w = e[max(0, int(a * 10)):int(b * 10)]
        return len(w) > 0 and float(w.max() - w.min()) < 0.2
    gets = [sg['get'] for sg in segments]
    n = 0
    for l in lines:
        if l.get('c') or l.get('a'):   # (a line whose time NASA's scan lost can't be placed that finely)
            continue
        k = bisect.bisect_right(gets, l['g']) - 1
        if k < 0:
            continue
        sg = segments[k]
        t = sg['from'] + (l['g'] - sg['get']) / sg['rate']
        if not (sg['from'] <= t <= sg['to']) or sg['tape'] not in tape_words or sg.get('journal'):
            continue
        starts = tape_words[sg['tape']][1]
        span = 6 + 0.3 * len(l['t'].split())
        if bisect.bisect_right(starts, t + span) == bisect.bisect_left(starts, t - 6) and flat(sg['tape'], t - 2, t + span):
            l['n'] = 1
            n += 1
    return n


