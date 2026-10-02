"""The public-affairs announcer on the tapes: finding him, moving misplaced announcements, marking talk-over."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np

from .common import from_liftoff
from .ocr_repair import LABELS  # noqa: F401 (defined there; the repair step uses it too)


NUMBER_WORDS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen '
    'seventeen eighteen nineteen'.split())}
NUMBER_WORDS.update({w: 10 * i for i, w in enumerate('_ _ twenty thirty forty fifty sixty seventy eighty ninety'.split()) if i >= 2})
_NUM = r"(?:\d|(?:" + '|'.join(sorted(NUMBER_WORDS, key=len, reverse=True)) + r")\b)"
_WHO = r"(?:apollo|mission) control,? (?:houston,? )?"
# "This is Apollo Control at 59 hours, 9 minutes" ("it's 66 hours one minute", "at 90 hours at 10 minutes");
# his sign-off "At 78 hours, 58 minutes ..., this is Apollo Control"; and each on the hour, with no minutes
# ("This is Apollo Control at 65 hours.", "At 67 hours, this is Apollo Control.")
SAID_TIME = [
    ('open', re.compile(_WHO + r"(?:at |it'?s |it is )?([\w -]+?) hours?,? (?:and |at |of |is )?([\w -]+?) minutes?\b", re.I)),
    ('close', re.compile(r"(?:at |)([\w -]+?) hours?,? (?:and )?([\w -]+?) minutes?\b[\w ,]*?,? this is (?:apollo|mission) control", re.I)),
    ('open', re.compile(_WHO + r"(?:at |it'?s |it is )([\w-]+(?: [\w-]+){0,3}?) hours?\b(?!,? (?:and |at |of |is )?" + _NUM + r")()", re.I)),
    ('close', re.compile(r"\bat ([\w-]+(?: [\w-]+){0,3}?) hours?,? this (?:is )?(?:apollo|mission) control()", re.I)),
]
LAST_HOUR = 320   # (Apollo 17 ran 302 hours, and Mission Control's clock 2:40 ahead of that)


RADIO_WORDS = {'roger', 'copy', 'okay', 'ok', 'affirmative', 'negative', 'wilco', 'readback'}


TITLES = re.compile(r"(?:Dr|Mr|Mrs|Ms|St|Jr|Sr|Gen|Col|Lt|Capt|Gov|Sen|Rep|vs|[B-HJ-Z])\.")   # (and a middle initial: "Thomas O. Paine")


# names the recogniser spells its own way in what the announcer says
ASR_NAMES = [(r"\bGlenn Lunney\b", 'Glynn Lunney'), (r"\bKrantz\b", 'Kranz'), (r"\bRusa\b", 'Roosa'),
             (r"\bShepherd\b", 'Shepard'), (r"\bErwin\b", 'Irwin'), (r"\bHennise\b", 'Henize'),
             (r"\bCarl Henize\b", 'Karl Henize'), (r"\bEndeavor\b", 'Endeavour')]


def spell_names(text):
    for pattern, name in ASR_NAMES:
        text = re.sub(pattern, name, text)
    return text


def ends_sentence(word):
    """A word that ends one of the announcer's sentences: a stop, but not a title's ("Dr. Paine") or an initial's."""
    w = word.strip()
    return w.endswith(('.', '?', '!')) and not TITLES.fullmatch(w)


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


def said_times(text):
    """Every mission time the announcer gives in `text`, in order: [(where
    in the text, seconds, 'open' or 'close')], 'open' for the time he starts
    an announcement with and 'close' for the one he signs off with."""
    found = []
    for kind, pattern in SAID_TIME:
        for m in pattern.finditer(text):
            h, mnt = m.group(1), m.group(2)
            # ("Apollo Control Houston, now 175 hours": a word or two before the figure, not a sentence
            # of them: "mission control here is showing a wake time 7 hours 22 minutes" is no announcement's time)
            h = (int(h.split()[-1]) if len(h.split()) <= 3 else None) if h.split()[-1].isdigit() else _number(h)
            mnt = _number(mnt) if mnt else 0
            if h is not None and mnt is not None and h < LAST_HOUR and mnt < 60:
                found.append((m.start(), m.end(), h * 3600 + mnt * 60, kind))
    found.sort()
    out, upto = [], -1
    for a, b, seconds, kind in found:
        if a >= upto:   # (one reading of each stretch of words)
            out.append((a, seconds, kind))
            upto = b
    return out


def said_time(text):
    """The mission time the announcer gives ("This is Apollo Control at 59
    hours, 9 minutes"), in seconds, and whether he says it at the start."""
    for at, seconds, _kind in said_times(text):
        return seconds, at < len(text) / 2
    return None, None


FAR_S = 12 * 3600      # an announcement on a placed tape is never moved further than this (a rest period is shorter)
OUT_OF_STEP_S = 240   # a time he gives this far from where the one before puts it: the recorder was stopped between them


def split_announcements(st):
    """One stretch of his speech as the announcements in it. Through a rest
    period the recorder ran only while he spoke, so the hourly announcements
    sit one after another on the tape with no gap, and are found as one
    stretch; the first time he gives would place them all. It's cut where a
    time he gives doesn't follow from the one before: at the start of the
    sentence that opens the later announcement ("This is Apollo Control at
    65 hours"), or, where it only signs off with its time, after the sign-off
    before it (else at his last "this is Apollo Control" between the two,
    else at the longest pause)."""
    words = st['words']
    starts, pos = [], 0
    for x in words:
        starts.append(pos)
        pos += len(x[2]) + 1
    text = ' '.join(x[2] for x in words)
    said = [(bisect.bisect_right(starts, at) - 1, from_liftoff(seconds), kind) for at, seconds, kind in said_times(text)]
    if len(said) < 2:
        return [st]

    def sentence_start(k, floor):
        while k > floor and not ends_sentence(words[k - 1][2]):
            k -= 1
        return k

    def sentence_end(k):
        while k + 1 < len(words) and not ends_sentence(words[k][2]):
            k += 1
        return k + 1

    toks = [re.sub(r"[^a-z]", '', x[2].lower()) for x in words]
    cuts = []
    for (i, s0, kind0), (j, s1, kind1) in zip(said, said[1:]):
        if abs(s1 - (s0 + (words[j][0] - words[i][0]) * st['rate'])) <= OUT_OF_STEP_S:
            continue
        lo = min(sentence_end(i), j)
        if kind1 == 'open':
            cut = sentence_start(j, lo)
        elif kind0 == 'close':
            cut = lo
        else:
            opens = [k for k in range(lo, j) if toks[k] == 'this' and toks[k + 1:k + 2] == ['is'] and toks[k + 2:k + 3] in (['apollo'], ['mission'])
                     and toks[k + 3:k + 4] == ['control'] and (k == 0 or ends_sentence(words[k - 1][2]))]
            cut = opens[-1] if opens else max(range(lo, j + 1), key=lambda k: words[k][0] - words[k - 1][1], default=None) if lo <= j else None
        if cut and (not cuts or cut > cuts[-1]) and cut < len(words):
            cuts.append(cut)
    if not cuts:
        return [st]
    pieces = []
    for a, b in zip([0] + cuts, cuts + [len(words)]):
        t0 = st['t0'] if a == 0 else words[a][0] - 0.3
        t1 = st['t1'] if b == len(words) else min(words[b - 1][1] + 0.3, words[b][0] - 0.3)
        last = b == len(words)
        pieces.append({**st, 't0': t0, 't1': max(t1, t0), 'get': st['get'] + (t0 - st['t0']) * st['rate'], 'words': words[a:b],
                       'over': st['over'] if last else None, 'over_words': st['over_words'] if last else []})
    return pieces


def find_announcer(segments, lines, tape_words, heard_at):
    """The public-affairs announcer on the tapes: NASA's air-to-ground tapes
    are the broadcast mix, with "This is Apollo Control ..." between (and
    sometimes over) the crew and the ground. Each announcement runs from the
    run of speech holding "this is Apollo Control" (or "Mission Control"),
    back and on through pauses shorter than 4 s, until a change of voice,
    NASA's next transcript line, or words of NASA's lines (three in a row:
    the crew's, never his). On past a pause of up to 10 s where what follows
    is more of the same (four words or more, none of NASA's), as he often
    stops to read the next figure; and back from a sign-off ("... at 65 hours,
    29 minutes, this is Apollo Control") to the start of that announcement.

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
    by_tape, grams = {}, {}   # NASA's lines on each tape: where they start (and how many words), and their runs of three words
    for l in lines:
        k = bisect.bisect_right(gets, l['g']) - 1
        if k >= 0 and l['g'] <= end(segments[k]):
            sg = segments[k]
            t = sg['from'] + (l['g'] - sg['get']) / sg['rate']
            words = re.findall(r"[a-z0-9]+", l['t'].lower())
            by_tape.setdefault(sg['tape'], []).append((t, len(words)))
            for j in range(len(words) - 2):
                grams.setdefault(sg['tape'], {}).setdefault(tuple(words[j:j + 3]), []).append(t)
    stretches = []   # {tape, t0, t1, words, get (at t0), rate}
    for sg in segments:
        if sg['tape'] not in tape_words:
            continue
        w = tape_words[sg['tape']][0]
        toks = [re.sub(r"[^a-z]", '', x[2].lower()) for x in w]
        here = sorted(by_tape.get(sg['tape'], []))
        starts_here = [t for t, _ in here]
        lo, hi = bisect.bisect_left([x[0] for x in w], sg['from']), bisect.bisect_right([x[0] for x in w], sg['to'])
        # words that are NASA's lines (three in a row as one of them has it, said within five minutes): the crew's
        nt = [re.sub(r"[^a-z0-9]", '', x[2].lower()) for x in w[lo:hi]]
        gr = grams.get(sg['tape'], {})
        crew = [False] * (hi - lo)
        for j in range(len(nt) - 2):
            if all(nt[j:j + 3]) and any(abs(t - w[lo + j][0]) < 300 for t in gr.get(tuple(nt[j:j + 3]), ())):
                crew[j] = crew[j + 1] = crew[j + 2] = True
        # (and radio talk he never uses: "Roger", "copy", a sentence ending "over")
        radio = lambda k: toks[k] in RADIO_WORDS or bool(re.fullmatch(r"over[.?!]", w[k][2].strip().lower()))
        is_crew = lambda k: crew[k - lo] or radio(k)
        i, floor = max(lo, 1), lo   # (floor: his first word no earlier than this, past his announcement before)
        while i < hi - 1:
            if not (toks[i] in ('apollo', 'mission') and toks[i + 1] == 'control' and toks[i - 1] in ('is', 'this')):
                i += 1
                continue
            # back to the start of his announcement: not into NASA's line before (its words, or the time it takes to say)
            prv = here[:bisect.bisect_left(starts_here, w[i][0] - 0.5)][-1:]
            before = prv[0][0] + 0.5 + 0.35 * prv[0][1] if prv else -1
            a = i
            while a > floor and toks[a - 1] not in LABELS and (
                    (w[a][0] - w[a - 1][1] < 1.5 and w[i][0] - w[a - 1][0] < 8)
                    or (w[a][0] - w[a - 1][1] < 4 and w[i][0] - w[a - 1][0] < 600 and w[a - 1][0] > before and not is_crew(a - 1))):
                a -= 1
            t0 = max(w[a][0] - 0.3, sg['from'])
            nxt = starts_here[bisect.bisect_right(starts_here, t0 + 2):][:1]
            b = i
            while True:
                while (b + 1 < hi and w[b + 1][0] - w[b][1] < 4 and toks[b + 1] not in LABELS
                       and (not nxt or w[b + 1][0] < nxt[0] - 0.5) and w[b + 1][0] - t0 < 600):
                    b += 1
                # past a pause, more of his: four words or more, none of them NASA's, before NASA's next line
                r = b + 1
                if not (r < hi and w[r][0] - w[b][1] < 10 and (not nxt or w[r][0] < nxt[0] - 0.5)):
                    break
                while r + 1 < hi and w[r + 1][0] - w[r][1] < 4 and (not nxt or w[r + 1][0] < nxt[0] - 0.5):
                    r += 1
                if (r - b < 4 or w[r][0] - t0 >= 600 or any(is_crew(k) or toks[k] in LABELS for k in range(b + 1, r + 1))):
                    break
                b = r
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
            i = floor = max(c if covers else b, tail) + 1

    # announcements recorded out of their time: out to the time he gives
    stretches = [piece for st in stretches for piece in split_announcements(st)]
    moved = []
    for st in stretches:
        spoken, at_start = said_time(' '.join(x[2] for x in st['words']))
        if spoken is None:
            continue
        spoken = from_liftoff(spoken)
        length = st['t1'] - st['t0']
        want = spoken + 20 if at_start else spoken + 40 - length
        if -90 <= st['get'] - want <= 150:
            continue
        if st['get'] > -5e6 and abs(st['get'] - want) > FAR_S:
            continue   # (on a placed tape, half a day from where he is: a time to an event misheard as the time, "3 hours 52 minutes remaining")
        moved.append((st, want))
    for st, want in moved:
        own = None
        for k, sg in enumerate(segments):   # cut it out of the piece it was in
            if sg['tape'] == st['tape'] and sg['from'] <= st['t0'] < sg['to']:
                own, rest = sg, []
                if st['t0'] - sg['from'] > 1:
                    rest.append({**sg, 'to': st['t0']})
                if sg['to'] - st['t1'] > 1:
                    rest.append({**sg, 'from': st['t1'], 'get': sg['get'] + (st['t1'] - sg['from']) * sg['rate']})
                segments[k:k + 1] = rest
                break
        length = st['t1'] - st['t0']
        in_the_way = lambda w: [sg for sg in segments if sg['get'] < w + length and end(sg) > w]
        block = in_the_way(want)
        for _ in range(6):   # behind announcements already put there (two that give the same minute): straight after them
            if not block or not all(sg.get('spoken') for sg in block):
                break
            want = max(end(sg) for sg in block) + 1
            block = in_the_way(want)
        if block and own is not None and not own.get('standin'):
            # another tape plays at the time he gives: it stays where it is on its own tape, not lost
            segments.append({**own, 'from': st['t0'], 'to': st['t1'], 'get': st['get']})
            continue
        st['get'], st['rate'] = (None, 1.0) if block else (want, 1.0)
        st['over'], st['over_words'] = None, []
        if not block:
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
            if ends_sentence(x[2]) or x is allw[-1]:
                extra = {'o': 1} if over_from is not None and start >= over_from else {}
                said.append({'g': round(g(start)), 's': 'Public Affairs', 't': spell_names(' '.join(sentence)), 'c': 'pao', **extra})
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


