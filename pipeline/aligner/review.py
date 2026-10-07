"""Which lines most need a person's ear: a ranked list for the reviewer.

Every line has up to three readings: NASA's typed transcript (as merged
from the scan's embedded text and Tesseract), and what the speech
recogniser heard on the tape at that moment. Where the readings agree the
line is almost certainly right; where they disagree, or where damage
survives repair, it's worth checking.

Each line gets a score 0-100 and, when high enough, a short reason the
reviewer can read at a glance: "3 damaged words", "tape hears 'not
lightning' for 'net lightning'". The list is written to
public/review/transcript/apolloNN.json for the reviewer page, and the
score travels with the line (key 'q') so the site can flag it too.
"""
import bisect
import difflib
import re

from .common import tokens
from .ocr_repair import _core, _suspect

# Words whose misreading looks like another real word: the dictionary
# can't catch these, only a second reading can.
LOOKALIKE_MAX_DIST = 2
# the same word as heard, spelled NASA's way (a CapCom's name, the CSM's British spelling)
SOUNDS_SAME = {('karl', 'carl'), ('endeavour', 'endeavor')}
# a word the scan plainly mangled: a stray mark or digit inside it ("w__", "2age", "tonsorial,les"), not just an unusual word ("wristrings")
GARBLE = re.compile(r"[^A-Za-z0-9'&/.\-]|[A-Za-z]\d|\d[A-Za-z]{2}")


def _heard_window(line, segments, tape_words, gets):
    """The recognised words spoken over this line: (list of lowercase words)
    or None if the line isn't on a tape piece."""
    k = bisect.bisect_right(gets, line['g']) - 1
    if k < 0:
        return None
    sg = segments[k]
    end = sg['get'] + (sg['to'] - sg['from']) * sg['rate']
    if not sg['get'] <= line['g'] <= end or sg['tape'] not in tape_words or sg.get('journal'):
        return None
    words, starts = tape_words[sg['tape']]
    t0 = sg['from'] + (line['g'] - sg['get']) / sg['rate']
    span = 4 + 0.45 * len(line['t'].split())
    lo, hi = bisect.bisect_left(starts, t0 - 2), bisect.bisect_right(starts, t0 + span)
    return [re.sub(r"[^a-z0-9']", '', w[2].lower()) for w in words[lo:hi]]


def _disagreements(nasa_words, heard):
    """Words where NASA's text and the tape's reading differ by only a letter
    or two: likely misreads that look like real words. [(nasa, heard)]."""
    out = []
    cores = [_core(w)[1] for w in nasa_words]
    # an acronym (LOS, G&N, AOS) is read out letter by letter and the
    # recogniser spells it any old way ("lls", "gnn"): not a misread
    acronym = [bool(re.fullmatch(r"[A-Z][A-Z&/]{1,4}s?", c)) for c in cores]
    mine = [c.lower() for c in cores]
    sm = difflib.SequenceMatcher(None, mine, heard, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != 'replace' or i2 - i1 != j2 - j1:
            continue
        for k, (a, b) in enumerate(zip(mine[i1:i2], heard[j1:j2])):
            if len(a) < 3 or len(b) < 3 or a == b or a.isdigit() or b.isdigit() or acronym[i1 + k] or (a, b) in SOUNDS_SAME:
                continue
            if 0 < sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b)) <= LOOKALIKE_MAX_DIST:
                out.append((a, b))
    return out


def suggest(text, heard, vocab, common=None):
    """A proposed reading of a damaged line from the words heard over it:
    each damaged word (per _suspect) that lines up with a heard word of the
    same shape (half its letters in order, or one letter off) takes that
    word, keeping NASA's punctuation and capital. Returns (text, changed)
    with changed as [(from, to)], or (text, []) when nothing changes."""
    words = text.split()
    cores = [_core(w) for w in words]
    mine = [c[1].lower() for c in cores]
    heard = [h for h in heard if h]
    if not heard:
        return text, []
    good = lambda h: h in vocab or (common is not None and h in common) or re.fullmatch(r"\d+", h)
    changed, out = [], list(words)
    sm = difflib.SequenceMatcher(None, [re.sub(r"[^a-z0-9']", '', m) for m in mine], heard, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != 'replace':
            continue
        used = set()
        for k in range(i1, i2):
            lead, core, trail = cores[k]
            if not _suspect(core, vocab) or core[:1].isupper() and core[1:].isalpha() and core.lower() in vocab:
                continue
            plain = re.sub(r"[^a-z0-9]", '', core.lower())
            if re.sub(r"[^a-z]", '', core.lower()) in vocab and len(plain) >= 4:
                continue   # (a stray mark on a sound word, "{Laughter": for the eye, not the tape)
            garbled = bool(GARBLE.search(core))
            best, score = None, 0.0
            for j in range(j1, j2):
                h = heard[j]
                if j in used or not good(h) or len(h) < 2:
                    continue
                if core.isalpha() and h in plain and len(h) < len(plain):
                    continue   # (a word NASA ran together, "wetwipes", "suitpants": not damage, and "wipes" isn't it)
                r = difflib.SequenceMatcher(None, plain, h, autojunk=False).ratio()
                # a word of letters alone that just isn't in the dictionary ("vesicular") only gives way
                # to a near-identical heard word that starts the same way
                if not garbled and (r < 0.8 or plain[:2] != h[:2]):
                    continue
                if r > score:
                    best, score, at = h, r, j
            if best is None or score < 0.6 or (len(best) <= 3 and score < 0.67):
                continue
            used.add(at)
            new = best[:1].upper() + best[1:] if core[:1].isupper() else best
            out[k] = lead + new + trail
            changed.append((core, new))
    return (' '.join(out), changed) if changed else (text, [])


def score_lines(lines, segments, tape_words, vocab, common=None):
    """Set line['q'] (0-100, higher = more doubtful) and line['why'] on lines
    worth a look. Returns the ranked list [(score, index, why)]."""
    gets = [sg['get'] for sg in segments]
    ranked = []
    for i, l in enumerate(lines):
        if l.get('c') or l.get('ok') or not l['t'].strip():
            continue
        words = l['t'].split()
        reasons, score = [], 0
        # a capitalised word that isn't damaged is a name (Alou, Valdespino): not our problem
        damaged = [w for w in words if _suspect(_core(w)[1], vocab)
                   and not (_core(w)[1][:1].isupper() and _core(w)[1][1:].isalpha())
                   and not re.fullmatch(r"\[?sic\]?|\d+/\d+(?:st|nd|rd|th)s?", _core(w)[1], re.I)]   # (NASA's [sic], "16/100ths")
        if damaged:
            score += min(60, 20 * len(damaged))
            reasons.append(f"{len(damaged)} damaged word{'s' if len(damaged) > 1 else ''}: {', '.join(damaged[:3])}")
        if l.get('a'):
            score += 15
            reasons.append('time lost in the scan')
        if l['s'] == 'Unknown':
            score += 10
            reasons.append('speaker unknown')
        heard = _heard_window(l, segments, tape_words, gets)
        if heard and len(words) >= 3:
            dis = [(a, b) for a, b in _disagreements(words, heard) if common is None or b in common]
            if dis:
                score += min(40, 15 * len(dis))
                reasons.append('; '.join(f"tape hears '{b}' for '{a}'" for a, b in dis[:3]))
            # the line's words largely absent from what's heard: mistimed, or not what was said
            mine = {_core(w)[1].lower() for w in words if len(_core(w)[1]) >= 4}
            if mine and len(mine & set(heard)) < 0.3 * len(mine):
                score += 20
                reasons.append("few of its words are heard where it's timed")
        if l.get('n'):
            score = max(score, 25)
            reasons.append('marked not on this recording')
        if l.get('review'):   # a question a hand fix asks a listener (Who's speaking?): first on the list
            score = 100
            reasons.insert(0, l['review'])
        if l.get('fixed') and not l.get('review'):
            # a listener's report has dealt with it (the words, the speaker, where it's heard, or that it isn't):
            # what the list would say of it they've already judged. Only garble still in it brings it back.
            garbled = [w for w in damaged if GARBLE.search(_core(w)[1])]
            if not garbled:
                continue
            score, reasons = min(60, 20 * len(garbled)) + 5, [f"{len(garbled)} damaged word{'s' if len(garbled) > 1 else ''}: {', '.join(garbled[:3])}"]
        if score >= 25:
            l['q'] = min(100, score)
            l['why'] = ' · '.join(reasons)
            if heard:
                l['tape'] = ' '.join(heard)   # (the review list's: what the tape says over it)
                proposed, changed = suggest(l['t'], heard, vocab, common)
                if changed:
                    l['suggest'] = proposed
            ranked.append((l['q'], i, l['why']))
    ranked.sort(key=lambda r: (not lines[r[1]].get('review'), -r[0], r[1]))   # (questions for a listener first)
    return ranked
