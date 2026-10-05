"""Timing NASA's lines to where they are heard on the tapes; rebuilding garbled lines; marking unheard ones."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np
from .common import tokens, MIN_WORDS
from .placement import find, find_start, _find_unique
from .ocr_repair import _suspect, _core
from .announcer import LABELS

EARLY_S = 300   # how long before NASA's printed time a long line is still looked for


def _speech_ends(at, j, n_words):
    """About when a line found at word j (of the heard words' times `at`) has
    been said: the end of that run of speech (pauses under 2 s), no longer
    than the line could take."""
    k, limit = j, at[j] + 2 + 0.6 * n_words
    while k + 1 < len(at) and at[k + 1] - at[k] < 2 and at[k + 1] <= limit:
        k += 1
    return at[k] + 0.5


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
        cursor, waiting = 0, []   # waiting: lines since the last one found that weren't: still at their printed times
        said_until = None         # about when the last line found has been said
        for i in sorted(idx, key=lambda i: lines[i]['g']):
            toks = tokens(lines[i]['t'])
            if len(toks) < MIN_WORDS:
                waiting.append(i)
                continue
            lo = max(cursor, bisect.bisect_left(at, lines[i]['g'] - 30))
            hi = bisect.bisect_right(at, lines[i]['g'] + 60)
            g, share = find_start(toks, heard, lo, hi) if lo < hi else (None, 0.0)
            early = False
            if (g is None or share < 0.6) and len(toks) >= 6:
                # a time NASA printed a minute or more late (Apollo 17's moonwalks: "04 23 58 52" on a line
                # said at 57:54): a long line clearly said earlier, after the line before it
                lo2, hi2 = max(cursor, bisect.bisect_left(at, lines[i]['g'] - EARLY_S)), min(len(heard), lo + len(toks))
                if lo2 < hi2:
                    # (its words together in one place, and no second place as good: over five minutes
                    # of talk a line's words turn up in order here and there by chance)
                    g, share = _find_unique(toks, heard, lo2, hi2)
                    if g is not None and share < 0.8:
                        g = None
                    early = g is not None
            if g is None or share < 0.6:
                waiting.append(i)
                continue
            j = bisect.bisect_left(at, g)
            if early:
                # the lines before it whose printed times are late too come back with it, in order: each to
                # where it's heard between the last line found and this one, or else to just before this one
                c, back, found = cursor, [q for q in waiting if lines[q]['g'] > g], {}
                for q in back:
                    tq = tokens(lines[q]['t'])
                    gq, sq = _find_unique(tq, heard, c, j) if len(tq) >= MIN_WORDS and c < j else (None, 0.0)
                    if gq is not None and sq >= 0.6:
                        found[q] = gq
                        c = bisect.bisect_left(at, gq) + max(1, int(0.7 * len(tq)))
                # (those not heard: spread over the gap between the lines heard either side of them, where
                # they were said; often a stretch the tape missed, and they're marked so there)
                kept = [lines[q]['g'] + 0.5 + 0.35 * len(tokens(lines[q]['t'])) for q in waiting if lines[q]['g'] <= g]
                left, gap = max([x for x in [said_until] + kept if x is not None], default=None), []   # (after the lines that stay before it)
                for q in back + [None]:
                    if q is not None and q not in found:
                        gap.append(q)
                        continue
                    right = found[q] if q is not None else g
                    lo_g = max(left if left is not None else right - 3 * len(gap), right - 60)
                    for k, u in enumerate(gap):
                        lines[u]['g'] = round(lo_g + (right - lo_g) * k / len(gap) if right - lo_g > 1 else right - 0.5, 1)
                        n += 1
                    gap = []
                    if q is not None:
                        lines[q]['g'] = round(found[q], 1)
                        left = _speech_ends(at, bisect.bisect_left(at, found[q]), len(tokens(lines[q]['t'])))
                        n += 1
            cursor, waiting = j + max(1, int(0.7 * len(toks))), []
            said_until = _speech_ends(at, j, len(toks))
            if abs(g - lines[i]['g']) >= 0.5:
                lines[i]['g'] = round(g, 1)
                n += 1
    return n


def heard_between(segments, tape_words, g0, g1):
    """The words heard on the tapes over mission time [g0, g1], in order,
    each as (mission time, ...the recognised word's other fields)."""
    end = lambda sg: sg['get'] + (sg['to'] - sg['from']) * sg['rate']
    heard = []
    for sg in segments:
        if end(sg) < g0 or sg['get'] > g1 or sg['tape'] not in tape_words or sg.get('journal'):
            continue
        words, starts = tape_words[sg['tape']]
        ta = sg['from'] + (max(g0, sg['get']) - sg['get']) / sg['rate']
        tb = sg['from'] + (min(g1, end(sg)) - sg['get']) / sg['rate']
        for w in words[bisect.bisect_left(starts, ta):bisect.bisect_right(starts, tb)]:
            heard.append((sg['get'] + (w[0] - sg['from']) * sg['rate'],) + tuple(w[1:]))
    heard.sort(key=lambda h: h[0])   # by time only: words the recogniser gave one time keep their order
    return heard


def retime(lines, segments, tape_words, which, before=45, after=120):
    """Time the given lines afresh, where their words are heard: from a
    little before their present time to two minutes after (a line whose
    time the scan lost sits at the time of the line before it). For lines a
    hand fix has corrected or split off, whose words now match the tape.
    The line is placed by the longest run of its words heard in order, not
    the first: a callsign it opens with ("Columbia, Houston") is often in
    the line before too; then back to its first words heard close before
    that run. Returns how many moved."""
    n = 0
    for l in lines:
        if id(l) not in which or l.get('n'):   # (a line marked not on this recording has nothing to find)
            continue
        toks = tokens(l['t'])
        if len(toks) < 2:
            continue
        on = which[id(l)] if isinstance(which, dict) else after
        heard = heard_between(segments, tape_words, l['g'] - before, l['g'] + on)
        sm = difflib.SequenceMatcher(None, toks, [h[3] for h in heard], autojunk=False)
        blocks = [b for b in sm.get_matching_blocks() if b.size]
        if not blocks:
            continue
        run = max(blocks, key=lambda b: b.size)
        # then back to its first words: a word the recogniser missed or misheard
        # breaks the run, so earlier stretches of the line heard just before it
        # count (a single word only as the line's opening)
        first = run
        for b in reversed(blocks[:blocks.index(run)]):
            if b.size < 2 and b.a > 2:
                continue
            if heard[first.b][0] - heard[b.b + b.size - 1][0] > first.a - (b.a + b.size) + 4:
                break
            first = b
        g, share = heard[first.b][0] - 0.3 * first.a, sum(b.size for b in blocks) / len(toks)
        if run.size >= 2 and (share >= 0.5 or run.size >= 5):   # (a long PAD runs past the window)
            if abs(g - l['g']) >= 0.5:
                n += 1
            l['g'] = round(g, 1)
            l.pop('a', None)
    return n


LONG_RUN = 8   # this many untimed lines in a row are lined up with the tape all together


def _align_run(lines, run, before, heard):
    """Times for a long run of untimed lines (Apollo 17 printed a time only
    where an exchange starts: a minute or five of talk follows each), by
    lining the whole run up with the words heard over its stretch at once:
    the longest stretches of matching words settle first and the rest fall
    in order between them. Looking for each line in turn after the one
    before (as for a short run) lets one short line found too far on
    ("Okay, that's good") carry every line after it past its place. The
    timed line before goes in with the run, to take its own words.
    A line is timed where at least 0.6 of its words fell in order, two of
    them together; returns how many were."""
    owner, flat = [], []
    for i in ([before] if before is not None else []) + list(run):
        for k, tok in enumerate(tokens(lines[i]['t'])):
            owner.append((i, k))
            flat.append(tok)
    if not flat or not heard:
        return 0
    sm = difflib.SequenceMatcher(None, flat, [h[3] for h in heard], autojunk=False)
    hits = {}
    for a, b, size in sm.get_matching_blocks():
        for d in range(size):
            i, k = owner[a + d]
            hits.setdefault(i, []).append((k, b + d))
    done, last = 0, lines[before]['g'] if before is not None else None
    for i in run:
        got, n = hits.get(i, []), len(tokens(lines[i]['t']))
        if not lines[i].get('a') or n < MIN_WORDS or len(got) < 0.6 * n:
            continue
        pair = next(((k, j) for (k, j), (k2, j2) in zip(got, got[1:]) if k2 == k + 1 and j2 == j + 1), None)
        if pair is None:
            continue
        g = round(heard[pair[1]][0] - 0.3 * pair[0])
        if last is not None:
            g = max(g, last)   # (in order)
        lines[i]['g'], last = g, g
        lines[i].pop('a', None)
        done += 1
    return done


def time_untimed(lines, segments, tape_words, other_loop=()):
    """Times for NASA's lines whose time the scan lost (or, on the
    moonwalks, printed as the day and hour only), from the tapes: between
    the timed lines either side, each is looked for in order among the words
    heard on the tape over that stretch. A long run is lined up all at once
    (_align_run), over the stretch to the next timed line of its own loop:
    the command module's lines (`other_loop`, ids), each with its printed
    time, sit in among a moonwalk's and would cut the stretch short.
    Returns how many were timed."""
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
        # (and if none of them is heard there, up to a quarter of an hour on, and
        # surer of each: timed lines from another loop can sit between them and
        # where they were said, as Apollo 14's 129:19, the LM's talk heard at 129:22)
        if len(run) >= LONG_RUN:
            n2 = next((i for i in range(n, len(lines)) if not lines[i].get('a') and id(lines[i]) not in other_loop), len(lines))
            far = max(lines[n2]['g'] if n2 < len(lines) else g0 + 3600, g0 + 60)
            mine = [i for i in range(p + 1, n2) if lines[i].get('a') and id(lines[i]) not in other_loop]
            # (to where the next timed line starts and no further: its words, and a second "Houston, Apollo 11. Over."
            # after it, aren't this run's)
            found = _align_run(lines, mine, p if p >= 0 else None, heard_between(segments, tape_words, g0 - 1, min(far, g0 + 3600)))
            done += found
            if found:
                continue
        for far, need, least in ((g1, 0.6, MIN_WORDS), (max(g1, g0 + 900), 0.8, 6)):
            heard = heard_between(segments, tape_words, g0, far)   # the tape words over [g0, far], in mission order
            heard_at = [h[0] for h in heard]
            cursor, found = 0, 0
            for i in run:
                toks = tokens(lines[i]['t'])
                if not lines[i].get('a') or len(toks) < least or cursor >= len(heard):
                    continue
                g, share = find_start(toks, heard, cursor, min(len(heard), cursor + 400 + 3 * len(toks)))
                if g is not None and share >= need:
                    lines[i]['g'] = round(g)
                    lines[i].pop('a', None)
                    cursor = bisect.bisect_right(heard_at, g)
                    done += 1
                    found += 1
            if found or far > g1 or not any(len(tokens(lines[i]['t'])) >= MIN_WORDS for i in run):
                break
    # still-untimed lines keep their place between their neighbours
    for i in range(1, len(lines)):
        if lines[i].get('a') and lines[i]['g'] < lines[i - 1]['g']:
            lines[i]['g'] = lines[i - 1]['g']
    return done


def _spoken(segments, tape_words, g0, g1):
    """The words on the tapes over mission time [g0, g1] as (start, end, token), in mission time."""
    end = lambda sg: sg['get'] + (sg['to'] - sg['from']) * sg['rate']
    out = []
    for sg in segments:
        if end(sg) < g0 or sg['get'] > g1 or sg['tape'] not in tape_words or sg.get('journal'):
            continue
        words, starts = tape_words[sg['tape']]
        ta = sg['from'] + (max(g0, sg['get']) - sg['get']) / sg['rate']
        tb = sg['from'] + (min(g1, end(sg)) - sg['get']) / sg['rate']
        for w in words[bisect.bisect_left(starts, ta):bisect.bisect_right(starts, tb)]:
            at = lambda t: sg['get'] + (t - sg['from']) * sg['rate']
            out.append((at(w[0]), at(w[1]), w[3]))
    return sorted(out)


def place_unfound(lines, segments, tape_words, skip=()):
    """Lines whose time the scan lost and whose words time_untimed couldn't
    find (too short to be sure of, or partly misheard) would all sit at the
    time of the line before them, and play that line. Each goes instead to
    where its words start, looked for loosely (two of them, or all of a
    short line, in order) once most of the line before has been said and
    before the next timed line; failing that, to where the tape's next
    stretch of speech starts after the line before; failing that, just
    after it. Lines in `skip` (the command module's own link) stay put.
    Returns how many moved."""
    moved = 0
    for i in range(1, len(lines)):
        l = lines[i]
        if not l.get('a') or id(l) in skip:
            continue
        p = lines[i - 1]
        nxt = next((x for x in lines[i + 1:] if not x.get('a') and id(x) not in skip), None)   # (the next timed line of its own loop)
        hi = nxt['g'] if nxt else p['g'] + 300
        words = [w for w in _spoken(segments, tape_words, p['g'] - 1, hi + 8) if w[0] >= p['g'] - 1]
        if not words:
            continue
        need = max(1, int(0.6 * len(tokens(p['t']))))   # (the line before, mostly said)
        toks = tokens(l['t'])
        seq = [w[2] for w in words]
        best, at = 0, None
        for j in range(min(need, len(words)), len(words)):
            if words[j][0] > hi + 5:
                break
            if seq[j] not in toks:
                continue
            sm = difflib.SequenceMatcher(None, toks, seq[j:j + len(toks) + 3], autojunk=False)
            got = sum(b.size for b in sm.get_matching_blocks())
            if got > best:
                best, at = got, j
        if at is not None and (best >= 2 and best >= 0.4 * len(toks) or best == len(toks)):
            g = words[at][0] - 0.2
        else:
            k = min(need, len(words)) - 1
            while k + 1 < len(words) and words[k + 1][0] - words[k][1] < 0.8:
                k += 1   # (to the end of that stretch of speech)
            # (NASA's printed time for the next line is often a few seconds early: the
            # speech that starts just after it can still be this line's)
            g = words[k + 1][0] - 0.2 if k + 1 < len(words) and words[k + 1][0] < hi + 5 else words[k][1] + 0.5
        g = round(min(max(g, p['g']), max(p['g'], hi - 0.3)), 1)   # (in order: never past the next timed line)
        if abs(g - l['g']) >= 0.5:
            l['g'] = g
            moved += 1
    return moved


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


# what the recogniser writes into silence and tones ("You", again and again; "Beep"): not speech
FILLER = {'you', 'beep'}


def mark_unheard(lines, segments, tape_words, envelopes):
    """NASA's lines that fall where the tape is silent: NASA transcribed the
    full air-to-ground loop, and these tapes are the broadcast copy, which
    sometimes missed a call. Marked 'n' (not on this recording).

    Silent means both: the recogniser heard no words there, and the tape's
    loudness is flat (the recogniser misses faint speech a listener can
    still make out). envelopes: folder of place_tapes' loudness envelopes
    (10 a second, normalised). Silence on these tapes varies by about 0.1;
    faint speech can vary by as little as 0.3. Or no words heard at all for
    a minute and a half either side, whatever the loudness (but the
    recogniser's "You" in silence): a stretch of hiss or carrier, not
    speech (Apollo 11's 186-AAA, nine minutes of it). (A hole of a minute or more
    in the recognition isn't enough on its own: the recogniser drops whole
    stretches of clear speech on its pass over a tape, Apollo 11's 99:24
    "The RCS hot-fire is complete" among them. Where the broadcast dropped
    to noise mid-sentence, Apollo 12's 359-AAA at 4:18, the lines inside
    are marked by hand.)"""
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
        if l.get('c') or l.get('a') or l.get('heard'):   # (a line whose time NASA's scan lost can't be placed that finely; one a listener heard)
            continue
        k = bisect.bisect_right(gets, l['g']) - 1
        if k < 0:
            continue
        sg = segments[k]
        t = sg['from'] + (l['g'] - sg['get']) / sg['rate']
        if not (sg['from'] <= t <= sg['to']) or sg['tape'] not in tape_words:
            continue
        starts = tape_words[sg['tape']][1]
        span = 6 + 0.3 * len(l['t'].split())
        near = tape_words[sg['tape']][0][bisect.bisect_left(starts, t - 90):bisect.bisect_right(starts, t + 90)]
        if bisect.bisect_right(starts, t + span) == bisect.bisect_left(starts, t - 6) and flat(sg['tape'], t - 2, t + span) \
                or not any(w[3] not in FILLER for w in near) and starts and t < starts[-1]:
            l['n'] = 1
            n += 1
    return n


def said_on_tape(l, segments, tape_words):
    """Three of the line's words in a row on the tape, somewhere near its time."""
    said = tokens(l['t'])
    seq = [h[3] for h in heard_between(segments, tape_words, l['g'] - 15, l['g'] + 15 + 0.5 * len(said))]
    grams = set(zip(seq, seq[1:], seq[2:]))
    return any(g in grams for g in zip(said, said[1:], said[2:]))


def mark_drowned_out(lines, segments, tape_words, run=6, minutes=5, share=0.2, other_loop=()):
    """NASA's lines where the tape plays something else: the broadcast
    sometimes carried a press conference live instead of the air-to-ground
    loop (Apollo 12, 130:34 to 130:58). The tape has speech there, but
    none of the conversation NASA transcribed. A run of at least `run`
    lines, over `minutes` or more, each with at most `share` of its words
    heard around it, is marked 'n' (not on this recording), with the short
    lines between them. A line of `other_loop` (ids: the command module's
    talk during a moonwalk, which NASA printed apart) is marked on its own:
    the tape plays the moonwalk there. Returns how many were marked."""
    judged, n = [], 0
    for i, l in enumerate(lines):
        if l.get('c') or l.get('n') or l.get('heard'):
            continue
        if id(l) in other_loop:
            if len(tokens(l['t'])) >= 3 and not said_on_tape(l, segments, tape_words):
                l['n'] = 1
                n += 1
            continue
        toks = [t for t in tokens(l['t']) if len(t) >= 4]
        if not toks:
            continue   # ("Go.", "Roger.": too short to judge, marked with their neighbours)
        heard = heard_between(segments, tape_words, l['g'] - 10, l['g'] + 20)
        if len(heard) < 5:
            judged.append((i, None))   # (a quiet tape is mark_unheard's business)
            continue
        words = {h[3] for h in heard}
        deaf = sum(t in words for t in toks) / len(toks) <= share
        judged.append((i, deaf))
    prev = None   # ("Roger." on that loop: with the line before it)
    for l in lines:
        if id(l) in other_loop:
            if not l.get('n') and not l.get('heard') and prev is not None and prev.get('n') and len(tokens(l['t'])) < 3:
                l['n'] = 1
                n += 1
            prev = l
    start = None
    for k, (i, deaf) in enumerate(judged + [(len(lines), False)]):
        if deaf:
            start = k if start is None else start
            continue
        if start is not None:
            a, b = judged[start][0], judged[k - 1][0]
            if k - start >= run and lines[b]['g'] - lines[a]['g'] >= minutes * 60:
                for l in lines[a:b + 1]:
                    if not l.get('c') and not l.get('n') and not l.get('heard'):
                        l['n'] = 1
                        n += 1
            start = None
    return n
