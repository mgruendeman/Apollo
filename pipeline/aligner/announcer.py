"""The public-affairs announcer on the tapes: finding him, moving misplaced announcements, marking talk-over."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np

from .ocr_repair import LABELS  # noqa: F401 (defined there; the repair step uses it too)


NUMBER_WORDS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen '
    'seventeen eighteen nineteen'.split())}
NUMBER_WORDS.update({w: 10 * i for i, w in enumerate('_ _ twenty thirty forty fifty sixty seventy eighty ninety'.split()) if i >= 2})
SAID_TIME = re.compile(r"apollo control,? (?:houston,? )?(?:at )?([\w -]+?) hours?,? (?:and )?([\w -]+?) minutes"
                       r"|(?:at |)([\w -]+?) hours?,? (?:and )?([\w -]+?) minutes[\w ,]*?,? this is apollo control", re.I)


def _number(text):
    """"59", "fifty-nine", "one hundred and two" -> int, else None."""
    text = text.strip().lower()
    if text.isdigit():
        return int(text)
    n, seen = 0, False
    for w in re.split(r"[\s-]+", text):
        if w in NUMBER_WORDS:
            n += NUMBER_WORDS[w]
            seen = True
        elif w == 'hundred':
            n = max(n, 1) * 100
        elif w != 'and':
            return None
    return n if seen else None


def said_time(text):
    """The mission time the announcer gives ("This is Apollo Control at 59
    hours, 9 minutes"), in seconds, and whether he says it at the start."""
    for m in SAID_TIME.finditer(text):
        h, mnt = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        h, mnt = _number(h.split()[-1] if h.split()[-1].isdigit() else h), _number(mnt)
        if h is not None and mnt is not None and h < 200 and mnt < 60:
            return h * 3600 + mnt * 60, m.start() < len(text) / 2
    return None, None


def find_announcer(segments, lines, tape_words, heard_at):
    """The public-affairs announcer on the tapes: NASA's air-to-ground tapes
    are the broadcast mix, with "This is Apollo Control ..." between (and
    sometimes over) the crew and the ground. Each announcement runs from the
    start of the speech holding "this is Apollo Control" until a pause of 4 s,
    a change of voice, or NASA's next transcript line.

    Through quiet hours the recorders were run only for the announcements,
    so one stretch of tape can hold announcements from hours apart. Where the
    time he gives disagrees with the tape piece he's in, the announcement is
    moved out to its own piece at the time he gives (dropped if another tape
    already covers that moment); `segments` is changed to match.

    Where he carries on past the start of one of NASA's lines, and that line
    can't be made out on the tape (heard_at: tape times of the lines that
    were), he's talking over it: that part can't be cut, so it's returned
    separately, and his words and the lines he covers are marked 'o'.

    Returns (spans, over, said): spans [[GET from, GET to]] the listener can
    skip, over [[GET from, GET to]] where he talks over the crew, and his
    words as transcript lines {g, s, t, c: 'pao'}, a sentence each."""
    end = lambda sg: sg['get'] + (sg['to'] - sg['from']) * sg['rate']
    gets = [sg['get'] for sg in segments]
    by_tape = {}
    for l in lines:
        k = bisect.bisect_right(gets, l['g']) - 1
        if k >= 0 and l['g'] <= end(segments[k]):
            sg = segments[k]
            by_tape.setdefault(sg['tape'], []).append(sg['from'] + (l['g'] - sg['get']) / sg['rate'])
    stretches = []   # {tape, t0, t1, words, get (at t0), rate}
    for sg in segments:
        if sg['tape'] not in tape_words:
            continue
        w = tape_words[sg['tape']][0]
        toks = [re.sub(r"[^a-z]", '', x[2].lower()) for x in w]
        starts_here = sorted(by_tape.get(sg['tape'], []))
        lo, hi = bisect.bisect_left([x[0] for x in w], sg['from']), bisect.bisect_right([x[0] for x in w], sg['to'])
        i = max(lo, 1)
        while i < hi - 1:
            if not (toks[i] == 'apollo' and toks[i + 1] == 'control' and toks[i - 1] in ('is', 'this')):
                i += 1
                continue
            a = i
            while a > lo and w[a][0] - w[a - 1][1] < 1.5 and w[i][0] - w[a - 1][0] < 8 and toks[a - 1] not in LABELS:
                a -= 1
            t0 = max(w[a][0] - 0.3, sg['from'])
            nxt = starts_here[bisect.bisect_right(starts_here, t0 + 2):][:1]
            b = i
            while (b + 1 < hi and w[b + 1][0] - w[b][1] < 4 and toks[b + 1] not in LABELS
                   and (not nxt or w[b + 1][0] < nxt[0] - 0.5) and w[b + 1][0] - t0 < 600):
                b += 1
            t1 = min(w[b][1] + 0.3, sg['to'])
            # does he carry on over a line nobody can make out?
            heard = heard_at.get(sg['tape'], [])
            c = b
            while (c + 1 < hi and w[c + 1][0] - w[c][1] < 4 and toks[c + 1] not in LABELS and w[c + 1][0] - t0 < 600
                   and not any(w[b][1] < h <= w[c + 1][0] + 0.5 for h in heard[bisect.bisect_left(heard, w[b][1]):][:1])):
                c += 1
            # (over the crew only when it's more than a word or a second's timing slack)
            covers = bool(nxt) and c - b >= 3 and w[c][1] - max(nxt[0], w[b][1]) >= 3
            tail = c if (c > b and not covers) else b   # a word or two past the next line: still his sentence
            stretches.append({'tape': sg['tape'], 't0': t0, 't1': t1, 'rate': sg['rate'],
                              'get': sg['get'] + (t0 - sg['from']) * sg['rate'],
                              'words': [x for x, tk in zip(w[a:tail + 1], toks[a:tail + 1]) if tk not in LABELS],
                              'over': (t1, min(w[c][1] + 0.3, sg['to'])) if covers else None,
                              'over_words': [x for x, tk in zip(w[b + 1:c + 1], toks[b + 1:c + 1]) if tk not in LABELS] if covers else []})
            i = max(c if covers else b, tail) + 1

    # announcements recorded out of their time: out to the time he gives
    moved = []
    for st in stretches:
        spoken, at_start = said_time(' '.join(x[2] for x in st['words']))
        if spoken is None:
            continue
        length = st['t1'] - st['t0']
        want = spoken + 20 if at_start else spoken + 40 - length
        if -90 <= st['get'] - want <= 150:
            continue
        moved.append((st, want))
    for st, want in moved:
        for k, sg in enumerate(segments):   # cut it out of the piece it was in
            if sg['tape'] == st['tape'] and sg['from'] <= st['t0'] < sg['to']:
                rest = []
                if st['t0'] - sg['from'] > 1:
                    rest.append({**sg, 'to': st['t0']})
                if sg['to'] - st['t1'] > 1:
                    rest.append({**sg, 'from': st['t1'], 'get': sg['get'] + (st['t1'] - sg['from']) * sg['rate']})
                segments[k:k + 1] = rest
                break
        covered = any(sg['get'] < want + (st['t1'] - st['t0']) and end(sg) > want for sg in segments)
        st['get'], st['rate'] = (None, 1.0) if covered else (want, 1.0)
        st['over'], st['over_words'] = None, []
        if not covered:
            segments.append({'tape': st['tape'], 'from': round(st['t0'], 2), 'to': round(st['t1'], 2), 'get': round(want, 2),
                             'rate': 1.0, 'anchors': 0, 'spoken': True})
    segments.sort(key=lambda sg: sg['get'])

    spans, over, said = [], [], []

    def sentences(words, over_words, g):
        """His words a sentence a line; a sentence that starts over the crew is marked 'o'."""
        sentence, over_from = [], (over_words[0][0] if over_words else None)
        allw = words + over_words
        for x in allw:
            if not sentence:
                start = x[0]
            sentence.append(x[2])
            if x[2].endswith(('.', '?', '!')) or x is allw[-1]:
                extra = {'o': 1} if over_from is not None and start >= over_from else {}
                said.append({'g': round(g(start)), 's': 'Public Affairs', 't': ' '.join(sentence), 'c': 'pao', **extra})
                sentence = []

    for st in stretches:
        if st['get'] is None:
            continue
        g = lambda t, st=st: round(st['get'] + (t - st['t0']) * st['rate'], 2)
        spans.append([g(st['t0']), g(st['t1'])])
        sentences(st['words'], st['over_words'], g)
        if st['over']:
            o0, o1 = g(st['over'][0]), g(st['over'][1])
            over.append([o0, o1])
            for l in lines:
                if o0 - 1 <= l['g'] <= o1 and not l.get('c') and not l.get('a'):
                    l['o'] = 1
    return spans, over, said


