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
    mine = [_core(w)[1].lower() for w in nasa_words]
    sm = difflib.SequenceMatcher(None, mine, heard, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != 'replace' or i2 - i1 != j2 - j1:
            continue
        for a, b in zip(mine[i1:i2], heard[j1:j2]):
            if len(a) < 3 or len(b) < 3 or a == b or a.isdigit() or b.isdigit():
                continue
            if 0 < sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b)) <= LOOKALIKE_MAX_DIST:
                out.append((a, b))
    return out


def score_lines(lines, segments, tape_words, vocab, common=None):
    """Set line['q'] (0-100, higher = more doubtful) and line['why'] on lines
    worth a look. Returns the ranked list [(score, index, why)]."""
    gets = [sg['get'] for sg in segments]
    ranked = []
    for i, l in enumerate(lines):
        if l.get('c') or not l['t'].strip():
            continue
        words = l['t'].split()
        reasons, score = [], 0
        # a capitalised word that isn't damaged is a name (Alou, Valdespino): not our problem
        damaged = [w for w in words if _suspect(_core(w)[1], vocab)
                   and not (_core(w)[1][:1].isupper() and _core(w)[1][1:].isalpha())]
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
        if score >= 25:
            l['q'] = min(100, score)
            l['why'] = ' · '.join(reasons)
            ranked.append((l['q'], i, l['why']))
    ranked.sort(key=lambda r: (-r[0], r[1]))
    return ranked
