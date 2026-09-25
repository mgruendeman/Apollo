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
CREW = {'11': {'CDR': 'Armstrong', 'CMP': 'Collins', 'LMP': 'Aldrin'},
        '12': {'CDR': 'Conrad', 'CMP': 'Gordon', 'LMP': 'Bean'},
        '14': {'CDR': 'Shepard', 'CMP': 'Roosa', 'LMP': 'Mitchell'},
        '15': {'CDR': 'Scott', 'CMP': 'Worden', 'LMP': 'Irwin'},
        '16': {'CDR': 'Young', 'CMP': 'Mattingly', 'LMP': 'Duke'},
        '17': {'CDR': 'Cernan', 'CMP': 'Evans', 'LMP': 'Schmitt'}}
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
    for t, g in sorted(anchors):
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


# NASA's text came through OCR: "We'11" for "We'll", "Ro6er", "Cha_lie", stray ")".
FIXES = ROOT / 'pipeline' / 'transcript_fixes.json'


DICT = Path('/usr/share/dict/words')
CONFUSED = {'6': 'gb', '0': 'o', '1': 'li', '5': 's', '8': 'b', 'c': 'oe', 'e': 'c', 'o': 'c', '_': 'abcdefghijklmnopqrstuvwxyz', ';': 't',
            'i': 'l', 'l': 'i', 't': 'c', 'E': 'G', '(': 'G', '!': 'l', '*': 'r', '$': 's', '%': 'r', ']': 'l', '}': 'h',
            '?': 'h', "'": 'lnh', '¢': 'vc', 'k': 'b', 'r': 'n'}
JOINERS = {'a', 'and', 'the', 'of', 'to', 'in', 'is', 'it', 'we', 'you', 'on', 'at', 'for', 'be', 'are'}
PAIRS = {'li': 'h', 'Li': 'H', 'rn': 'm', 'ii': 'u', 'Ii': 'H', 'cl': 'd', 'vv': 'w'}
JUNK_TAIL = re.compile(r"^(.*?[.?!])(\s+\S*[^A-Za-z0-9\s.,?!'\-]\S*(?:\s+\S+)*|\s+[A-Z_]{3,}\S*(?:\s+\S+)*)\s*$")


def _words_in(text, vocab):
    """Whether a stretch of text is mostly real words (not OCR junk)."""
    real = sum(1 for w in re.findall(r"[A-Za-z]{3,}", text) if w.lower() in vocab)
    return real >= len(text.split()) / 3 or len(text.split()) > 4 or bool(re.search(r"\d{3}", text))


HEADING = re.compile(r"\s*(?:[A-Z}\]_& ]{2,}\s*)?\(\s*R\s*[EeVv ]*[\dlIi]+\s*\)\s*$"   # station: VANGUARD (REV 1)
                     r"|\s+[?FP]age\s+[\dO\]l1]+\s*$"                                   # page footer: Page 3
                     r"|\s+[A-Z_]{3,}[A-Z_ ]*\s*\(\s*'?R[^)]{0,6}\)?\s*\.?\s*$")                # CANARY ('REV 2)                                    # page footer: Page 3


def vocabulary(tape_words):
    """English words (the system word list) and every word the recogniser
    heard at least twice on this mission's tapes (names, jargon); and which
    of them are names, written with a capital."""
    listed = DICT.read_text(errors='ignore').split() if DICT.exists() else []
    lower = {w for w in listed if w.islower()}
    names = {w.lower() for w in listed if w[:1].isupper()} - lower
    from collections import Counter
    heard = Counter(re.sub(r"[^a-z0-9']", '', w[2].lower()) for tw, _ in tape_words.values() for w in tw)
    vocab = lower | names | {w for w, n in heard.items() if n >= 2 and w}
    common = lower | {w for w, n in heard.items() if n >= 5 and w}
    spoken = {w for w, n in heard.items() if n >= 3 and w}   # words actually said on these tapes
    return vocab, names, common, spoken


def _core(word):
    """A word without its surrounding punctuation: (lead, core, trail)."""
    m = re.match(r"^([\"(]*)(.*?)([.,?!;:\"')]*)$", word)
    return m.group(1), m.group(2), m.group(3)


def _suspect(core, vocab):
    """OCR damage: a character no word has ("_", "]", "%"), a digit or stray
    punctuation inside a lowercase word ("Ro6er", "cor.firmed"), or a word
    not in the dictionary ("Eone", "ccmplete"). Codes and callsigns
    ("SPS/G&N", "P76's", "TEI-4", "DELTA-V") are left alone."""
    if not core:
        return False
    letters = re.sub(r"[^A-Za-z]", '', core)
    if not letters or re.fullmatch(r"[A-Z]+s", letters) or letters.isupper() and len(letters) <= 4:
        return False   # codes: SEP, AOS, DSKY (damaged or not, no guessing)
    if re.search(r"[^A-Za-z0-9'.,?!;:/&\-]", core) or re.match(r"[;:,.][a-z]", core):   # ";he"
        return True
    if letters.isupper() or re.fullmatch(r"(?:Mc|Mac|O')[A-Z][a-z]+", core):   # McGhee
        return False
    if re.fullmatch(r"(?:[A-Za-z]\.)+[A-Za-z]?", core):   # p.m, U.S
        return False
    if re.search(r"[a-z][\d.,;:/?!%][a-z]|[a-z]\d|\d[a-z]{2}", core):
        return True
    if re.search(r"[a-z]'(?!(?:s|t|d|m|ll|re|ve)$)[a-z]", core) and core.lower() not in vocab:   # "e'aable" (not o'clock)
        return True
    w = core.lower()
    return core.isalpha() and len(core) >= 4 and w not in vocab and not (w.endswith('s') and w[:-1] in vocab)


def _clean(core):
    """A plain word that's only unfamiliar, not visibly damaged."""
    return core.isalpha()


def _similar(a, b):
    return difflib.SequenceMatcher(None, re.sub(r"[^a-z]", '', a.lower()), b).ratio()


def _unconfuse(core, vocab, freq=None, context=None):
    """The one dictionary word an OCR misreading could stand for, if exactly
    one fits ("Sta6ing" -> "Staging", "Cha_lie" -> "Charlie"), else None."""
    found = set()
    if core.isalpha() and len(core) >= 6:   # a little word run into the next ("andsatisfactory")
        for i in range(1, 5):
            a, b = core[:i].lower(), core[i:].lower()
            if a in JOINERS and b in vocab and len(b) >= 4:
                found.add(f'{a} {b}')
    if core.endswith('_') and len(core) >= 5 and core[:-1].lower() in vocab:   # "Roger_": punctuation, or a lost letter; can't tell
        return None
    spots = [i for i, ch in enumerate(core) if ch in CONFUSED]
    if len(spots) > 8:
        return None
    for i in spots:
        if core[i] == '_' and len(core) < 4:   # a missing letter in a short word could be anything
            continue
        for alt in CONFUSED[core[i]]:
            cand = core[:i] + alt + core[i + 1:]
            if cand.lower() in vocab and cand.isalpha():
                found.add(cand.lower())
    for pair, alt in PAIRS.items():
        i = core.find(pair)
        if i >= 0:
            cand = core[:i] + alt + core[i + 2:]
            if cand.lower() in vocab and cand.isalpha():
                found.add(cand.lower())
    if len(found) == 1:
        return found.pop()
    found -= {w for w in found if "'" in w and "'" not in core}
    if freq and found:   # several fit ("re_d": read, reed, rend): the one that goes with the words
        # either side of it in this mission's speech, else the one it says far more often
        if context:
            prev, nxt, pairs = context
            fit = {w: pairs.get((prev, w), 0) + pairs.get((w, nxt), 0) for w in found}
            ranked = sorted(found, key=lambda w: -fit[w])
            if fit[ranked[0]] >= 2 and fit[ranked[0]] >= 3 * fit[ranked[1]]:
                return ranked[0]
        ranked = sorted(found, key=lambda w: -freq.get(w, 0))
        if freq.get(ranked[0], 0) >= 3 and freq.get(ranked[0], 0) >= 3 * freq.get(ranked[1], 0):
            return ranked[0]
    return None


# Stations, callsigns and ships OCR mangles most ("iicuston", "Tar_n_ri_e").
PLACES = ['Apollo', 'Houston', 'Tananarive', 'Carnarvon', 'Canary', 'Goldstone', 'Guaymas', 'Honeysuckle', 'Hawaii',
          'Vanguard', 'Madrid', 'Texas', 'Bermuda', 'Redstone', 'Mercury', 'Ascension', 'Canberra', 'Guam', 'Antigua',
          'Goddard']
CALLSIGNS = {'11': ['Columbia', 'Eagle', 'Tranquility', 'Hornet'], '12': ['Clipper', 'Yankee', 'Intrepid', 'Hornet'],
             '14': ['Kitty', 'Hawk', 'Antares', 'Mauro', 'Orleans'], '15': ['Endeavour', 'Falcon', 'Hadley', 'Okinawa'],
             '16': ['Casper', 'Orion', 'Descartes', 'Ticonderoga'], '17': ['America', 'Challenger', 'Taurus', 'Littrow', 'Ticonderoga']}
MISSION = {'n': '11'}   # the mission being processed (set in main)
DIGIT_LOOKS = {'1': '[1!il|It]', '2': '[2Zz]', '4': '[4hA]', '5': '[5sS]', '6': '[6bG]', '7': '[7T]', '0': '[0oO]'}


def _place(word):
    """The station or callsign a damaged word stands for, if it's close."""
    letters = re.sub(r"[^a-z]", '', word.lower())
    if len(letters) < 4:
        return None
    places = PLACES + CALLSIGNS.get(MISSION['n'], [])
    best = max(places, key=lambda p: difflib.SequenceMatcher(None, letters, p.lower()).ratio())
    ratio = difflib.SequenceMatcher(None, letters, best.lower()).ratio()
    if word[:1].isupper() or word[:1] in 'lti':   # names start with a capital (or its misreading: "tlouston")
        return best if ratio >= 0.72 else None
    return best if not word[:1].isalpha() and ratio >= 0.8 else None   # "}:ouston": the capital lost to junk


CAPS = {'n': set()}   # this mission's all-capitals words (switch names, codes) seen often: CRYO, PRESS, PYRO


def _caps(word):
    """A damaged all-capitals word ("PYP0", "!RESS", "REPPgSS") as the one it's close to."""
    lead, core, trail = _core(word)
    letters = re.sub(r"[^A-Za-z0-9]", '', core)
    if len(letters) < 4 or core in CAPS['n'] or sum(ch.isupper() for ch in letters) < len(letters) - 2:
        return word
    if "'" in core or '-' in core or not re.search(r"[0!|_%$¢{}\[\]()]|[A-Z][a-z][A-Z]", core):
        return word   # a clean code ("DELTA-V", "PAD's", a rare one): leave it
    best = max(CAPS['n'], key=lambda c: difflib.SequenceMatcher(None, letters.upper(), c).ratio(), default=None)
    if best and abs(len(best) - len(letters)) <= 1 and difflib.SequenceMatcher(None, letters.upper(), best).ratio() >= 0.75:
        return lead + best + trail
    return word


def _places(text, vocab):
    """Mend damaged station names and callsigns, one word or two run apart
    ("Ho mton"), and "this is Horton" where it can only be Houston."""
    words = text.split()
    out, i = [], 0
    while i < len(words):
        lead, core, trail = _core(words[i])
        damaged = _suspect(core, vocab) or bool(re.search(r"[^A-Za-z']", core))
        if i + 1 < len(words) and re.fullmatch(r"[A-Z][A-Za-z_]{0,3}", core) and not trail and core.lower() not in JOINERS | {'this'}:
            l2, c2, t2 = _core(words[i + 1])
            joined = _place(core + c2)
            if joined and c2.lower() not in vocab and (_suspect(c2, vocab) or re.search(r"[^A-Za-z']", c2)):
                out.append(lead + joined + t2)
                i += 2
                continue
        known = PLACES + CALLSIGNS.get(MISSION['n'], [])
        fix = _place(core) if damaged and core not in known else None
        if fix is None and core not in known and len(out) >= 2 and out[-2].lower() == 'this' and out[-1].lower() == 'is' \
                and core[:1].isupper() and difflib.SequenceMatcher(None, core.lower(), 'houston').ratio() >= 0.6:
            fix = 'Houston'
        out.append(lead + fix + trail if fix else _caps(words[i]))
        i += 1
    return ' '.join(out)


def _scrap_tail(text):
    """Drop a line's closing run of scraps (no two letters or digits
    together, not NASA's "..."), when it holds an OCR-junk character."""
    toks = text.split()
    k = len(toks)
    while k > 1 and not re.search(r"[A-Za-z0-9]{2}", toks[k - 1]) and toks[k - 1] not in ('...', '-', '- -', '--'):
        k -= 1
    tail = ' '.join(toks[k:])
    if k < len(toks) and k > 0 and re.search(r"['\"}{_/;:|<>~^]", tail):
        return ' '.join(toks[:k])
    return text


def n_of_mission():
    return str(int(MISSION['n']))


def _tidy(text, vocab):
    """The plain slips, no tape needed."""
    text, n = HEADING.subn('', text)
    if n and text and text[-1].isalnum():
        text += '.'                                                           # "Roger, out TAN_NARIVE (RE_ 2)."
    text = JUNK_TAIL.sub(lambda m: m.group(1) if not _words_in(m.group(2), vocab) else m.group(), text)
    text = re.sub(r"^(?!\.\.\.)[.,;:'\s]+(?=[A-Z])", '', text)             # ".., We're"
    text = re.sub(r",\s*$", '.', text)                                     # a line ending "Over,"
    text = re.sub(r"(?<=\s)_(?=\d)|(?<=\d)_(?=\s|$)", '', text)            # "_103.0"
    n = str(int(MISSION['n']))                                                  # the mission's number, as OCR misreads it
    looks = ''.join(DIGIT_LOOKS.get(ch, ch) for ch in n)
    text = re.sub(r"\bApollo\s+" + looks + r"\b", 'Apollo ' + n, text)          # "Apollo !1", "Apollo lZ"
    text = re.sub(r"\bAp[\w_!|]{2,5}\s+(?:" + looks + ('|[o0l1!|iI]{2,3}' if n == '11' else '') + r")\b(?=,|\s)",
                  'Apollo ' + n, text)                                          # "Apo_I_ 11", "ApQiI oll"
    text = re.sub(r"\bC[O0][_{}\[\]M]{1,3}\s+TECH\b", 'COMM TECH', text)
    if n == '11':
        text = re.sub(r"(?<![\w-])[!|][1l](?=[,.\s]|$)", '11', text)          # "!1,"
    text = re.sub(r"\bS[_-]?[bh]and\b", 'S-band', text)
    text = re.sub(r"\bP[O0][O0]\b", 'P00', text)                           # program 00 ("P-zero-zero")
    text = re.sub(r"(?<=[A-Za-z'])11\b|\b11(?=[a-z])", 'll', text)
    text = re.sub(r"(?<=[A-Za-z'])1(?=[a-z])", 'l', text)
    text = re.sub(r"\b(\w+) _(re|ve|s|d)\b", r"\1'\2", text)               # "we _re" for "we're"
    text = re.sub(r"(?<=[.?!] )(?:Ore\W{0,3}\w?\W{0,3}|Ov[a-z_]r|[O0][v%]er|\(_ver|Ovor|\(\)ve[ir]')\.?$", 'Over.', text)   # "Ore r." for "Over."
    text = re.sub(r"(?<![\w(])[(G]0\b", 'GO', text)                       # "(0" / "G0" for GO
    text = re.sub(r"\b(?!O\d\b)[\dlO]*\d[\dlO.]*\b", lambda m: m.group().replace('l', '1').replace('O', '0'), text)   # lO1.4 (not O2)
    text = re.sub(r"(?<![\d\s]\s)(?<!\d)\b02\b(?=\s+[A-Za-z])", 'O2', text)   # oxygen: "02 fans", "02 valve" (not "02 25 30")
    text = re.sub(r"(?<=\d\.)\(", '0', text)                               # "4.(" for 4.0
    text = re.sub(r"(?<=\d\.)!", '1', text)                                 # "0.!" for 0.1
    text = re.sub(r"\bG\(\)", 'GO', text)                                  # "G()"
    text = re.sub(r"\s/(?=\s)", '', text)                                   # a lone "/"
    text = re.sub(r"\bOve r\b", 'Over', text)                               # "Ove r."
    text = re.sub(r"\b([a-z]{1,})([A-Z])([a-z]*)\b",                          # "tO", "bY", "oF", "floodliMht"
                  lambda m: (m.group(1) + m.group(2).lower() + m.group(3)) if (m.group(1) + m.group(2) + m.group(3)).lower() in vocab
                  else m.group(), text)
    text = re.sub(r"\b([A-Za-z]+)V(s|ll|re|ve|d|t|m)\b",                      # "ItVs" for "It's"
                  lambda m: m.group(1) + "'" + m.group(2) if (m.group(1) + "'" + m.group(2)).lower() in vocab else m.group(), text)
    text = re.sub(r"\b[GOQ0][o0]\s?ahead,?\s?(?=[A-Z])", 'Go ahead, ', text)    # "Qoahead,Houston"
    text = re.sub(r"\b[OQ0]o ahead\b", 'Go ahead', text)                       # "Oo ahead"
    text = re.sub(r"\b(from|the|of|to|and)-(the|a|an)\b", r"\1 \2", text)       # "from-the Sun"
    text = re.sub(r"\s[?FP]age\s+[\dO\]lt1I]{2,4}(?=\s)", '', text)           # a page number mid-line: "Page ]1t7"
    text = re.sub(r"\b(REPRESS|DIRECT|PLSS|cabin) 02\b", r"\1 O2", text)
    if not re.search(r"(^|\s)'\w", text):                                     # "the' Persian Gulf'": closing quotes never opened
        text = re.sub(r"(?<=[a-rt-z])'(?=[\s.,?!]|$)", '', text)
    text = re.sub(r"\b([NOH]) 2\b", r"\g<1>2", text)                        # "N 2 tank" for N2
    text = re.sub(r"\bPYRO bus\b", 'pyro bus', text)                         # (NASA wrote it both ways)
    text = re.sub(r"(?<=, )[Ili1!|]{2}(?=\.?$)", n_of_mission(), text)        # "..., Ii." for 11
    text = re.sub(r"^(Roger)\.?\s+[il1|]\s+[il1|]\.?$", r"\1.", text)          # "Roger. i i"
    text = re.sub(r"\b(Roger) r\s*\.", r"\1.", text)                          # "Roger r ."
    text = _scrap_tail(text)                                                  # "... descent. ',F? , }_ /'"
    text = re.sub(r"\s+\S{0,3}(?:[a_g<]e|ag[eo]|_ge)\s+\d{3,4}\s*$", '', text)  # page numbers: "}'_ge 307", "iago 312"
    text = re.sub(r"\b([A-Za-z]{3,})- ([a-z]{2,})\b",                         # "sequenc- ing": split at a line end
                  lambda m: m.group(1) + m.group(2) if (m.group(1) + m.group(2)).lower() in vocab else m.group(), text)
    text = re.sub(r"\b(primary|secondary|number|bus|gimbal|motor|quad|tank|bottle|loop|step|channel|position|option|"
                  r"battery|stage|NOUN|VERB|PAD|Program)\s+[liI|](?=[\s.,?;]|$)", r"\1 1", text)   # "primary l", "number i"
    text = re.sub(r"\b(one|two|three|four|five)-(?:by|ky|hy|bv|b_|_y|6y)-([\w_]{2,6})\b",   # "five-ky-two", "five-by-_ive"
                  lambda m: m.group(1) + '-by-' + max(['one', 'two', 'three', 'four', 'five'],
                                                      key=lambda w: difflib.SequenceMatcher(None, w, m.group(2).lower()).ratio()), text)
    text = re.sub(r"\b([a-z]+'[a-z])([A-Z])\b", lambda m: m.group(1) + m.group(2).lower(), text)   # "you'lL"
    n = str(int(MISSION['n']))
    text = re.sub(r"^" + ''.join(DIGIT_LOOKS.get(ch, ch) for ch in n) + r"(?=,)", n, text)   # a line opening "il," for 11
    # stray apostrophes: "In'reference" (two words), "'your question" (no closing quote)
    text = re.sub(r"\b([A-Za-z]{2,})'([a-z]{3,})\b", lambda m: m.group(1) + ' ' + m.group(2)
                  if m.group(1).lower() in vocab and m.group(2) in vocab and m.group(2) not in ('ll', 're', 've') else m.group(), text)
    if text.count("'") % 2 == 1 and not re.search(r"\s'\w.*\w'(\s|$|[.,?])", text):
        text = re.sub(r"(?<=\s)'(?=[a-z]{3,})", '', text)                    # an opening quote never closed
    text = re.sub(r"\b[A-Z][A-Z0-9]{2,}\b", lambda m: m.group().replace('0', 'O') if re.fullmatch(r"[A-Z]+0[A-Z]*", m.group()) else m.group(), text)   # CRY0
    text = re.sub(r"\b([A-Z]+[a-z]+[A-Z]*[a-z]*)\b",                       # HoUSton, OVer
                  lambda m: m.group().capitalize() if m.group().lower() in vocab else m.group(), text)
    if text.count('(') < text.count(')'):
        text = re.sub(r"\s+\)(?=\s|$)", '', text)
    return text.strip()


def repair_ocr(lines, segments, tape_words):
    """Mend OCR damage in NASA's lines, from what the tapes say.

    For each line on a tape, its words are matched in order against the
    recognised words at that moment; a damaged word ("Ro6er", "Eone") takes
    the recognised word it lines up with when they're close in spelling.
    Before that, a misreading that can only be one word is corrected
    ("Sta6ing"); anything else stays as NASA printed it."""
    vocab, names, common, spoken = vocabulary(tape_words)
    from collections import Counter as _C
    caps = _C(w for l in lines for w in re.findall(r"(?<![\w_])[A-Z]{3,}(?![\w_])", l['t']))
    CAPS['n'] = {w for w, k in caps.items() if k >= 4}
    from collections import Counter
    freq = Counter(re.sub(r"[^a-z0-9']", '', w[2].lower()) for tw, _ in tape_words.values() for w in tw)
    freq.update(w.lower() for l in lines for w in re.findall(r"(?<![\w_])[A-Za-z']+(?![\w_])", l['t']))
    pairs = Counter()   # which words follow which, in the recognised speech and NASA's clean words
    for tw, _ in tape_words.values():
        ws = [re.sub(r"[^a-z0-9']", '', w[2].lower()) for w in tw]
        pairs.update(zip(ws, ws[1:]))
    for l in lines:
        ws = [w.lower() for w in re.findall(r"(?<![\w_])[A-Za-z']+(?![\w_])", l['t'])]
        pairs.update(zip(ws, ws[1:]))

    def cased(word, original, i, words):
        """Capital for a sentence's first word, a name, or an unknown word
        (a callsign) printed with one."""
        letters = re.sub(r"[^A-Za-z]", '', original)
        if len(letters) >= 2 and letters.isupper():
            return word.upper()
        first = i == 0 or words[i - 1].endswith(('.', '?', '!'))
        if first or word in names or (original[:1].isupper() and original[:1] not in CONFUSED):
            return word.capitalize()
        return word
    gets = [sg['get'] for sg in segments]
    changed = 0
    for line in lines:
        words = _tidy(line['t'], vocab).split()
        bad = {i for i, w in enumerate(words) if _suspect(_core(w)[1], vocab)}
        # a misreading that can only be one word, first ("Sta6ing" -> "staging")
        for i in sorted(bad):
            lead, core, trail = _core(words[i])
            ctx = (_core(words[i - 1])[1].lower() if i else '', _core(words[i + 1])[1].lower() if i + 1 < len(words) else '', pairs)
            fix = _unconfuse(core, spoken | names if core[:1].isupper() else spoken, freq, ctx)   # (names only for a capital)
            if fix:
                words[i] = lead + cased(fix, core, i, words) + trail
                bad.discard(i)
                changed += 1
        k = bisect.bisect_right(gets, line['g']) - 1
        if bad and k >= 0:
            sg = segments[k]
            t = sg['from'] + (line['g'] - sg['get']) / sg['rate']
            if sg['from'] - 5 <= t <= sg['to'] + 5 and sg['tape'] in tape_words:
                tw, starts = tape_words[sg['tape']]
                span = tw[bisect.bisect_left(starts, t - 45):bisect.bisect_right(starts, t + 20 + 0.6 * len(words))]
                heard = [re.sub(r"[^a-z0-9']", '', w[2].lower()) for w in span]
                mine = [_core(w)[1].lower() for w in words]
                for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, mine, heard, autojunk=False).get_opcodes():
                    if op != 'replace':
                        continue
                    for i in range(i1, i2):
                        if i not in bad:
                            continue
                        lead, core, trail = _core(words[i])
                        if i2 - i1 == j2 - j1:   # word for word: the tape's word in the same place
                            options, need = [heard[j1 + i - i1]], (0.75 if _clean(core) else 0.5)
                        else:
                            options, need = heard[j1:j2], (0.75 if _clean(core) else 0.7)
                        options = [h for h in options if h in vocab and (h in common or h in names)]
                        best = max(options, key=lambda h: _similar(core, h), default=None)
                        if best and _similar(core, best) >= need:
                            words[i] = lead + cased(best, core, i, words) + (trail[1:] if "'" in best and trail[:1] == "'" else trail)
                            bad.discard(i)
                            changed += 1
                # A garbled stretch between words that match the tape on both
                # sides ("in tho F_ro(!_;__low and"): what the tape says there.
                ops = difflib.SequenceMatcher(None, [_core(w)[1].lower() for w in words], heard, autojunk=False).get_opcodes()
                swaps = []
                for q, (op, i1, i2, j1, j2) in enumerate(ops):
                    if op != 'replace' or not 1 <= j2 - j1 <= 2 * (i2 - i1) + 1:
                        continue
                    before = ops[q - 1] if q else None
                    after = ops[q + 1] if q + 1 < len(ops) else None
                    held = lambda o: o is not None and o[0] == 'equal' and o[2] - o[1] >= 2
                    if not (held(before) and (held(after) or i2 == len(words)) or held(after) and i1 == 0 and before is None):
                        continue
                    if any(re.search(r"\d", words[i]) for i in range(i1, i2)):
                        continue   # numbers are NASA's to keep: the recogniser spells them ("two two", "Niner")
                    damaged = [i for i in range(i1, i2) if re.search(r"[^A-Za-z'.,?!\-]", _core(words[i])[1])]   # visibly
                    if len(damaged) * 2 < i2 - i1 or not all(_suspect(_core(words[i])[1], vocab) for i in range(i1, i2)):
                        continue   # (a real word in the stretch, like DECA, stays NASA's)
                    new = [re.sub(r"[.,?!]+$", '', w[2]) for w in span[j1:j2] if re.sub(r"[^a-z]", '', w[2].lower()) not in LABELS]
                    if not new or not all(re.sub(r"[^a-z']", '', w.lower()) in common for w in new):
                        continue   # the recogniser's odd words ("iPad" for PAD) aren't trusted here
                    new[-1] += _core(words[i2 - 1])[2]
                    swaps.append((i1, i2, new))
                for i1, i2, new in reversed(swaps):
                    words[i1:i2] = new
                    bad = {i for i in bad if i < i1} | {i - (i2 - i1) + len(new) for i in bad if i >= i2}
                    changed += len(new)
        for i in sorted(bad):   # "Roger_" that nothing settled: the "_" was punctuation
            if words[i].endswith('_') and len(words[i]) >= 5 and words[i][:-1].lower() in vocab:
                words[i] = words[i][:-1]
        text = _places(' '.join(words), vocab)
        if text and text[-1].isalnum() and line['t'].rstrip()[-1:] in '.?!':   # a repair that took the full stop
            text += '.'
        line['t'] = text
    return changed


LABELS = {'capcom', 'sc', 'cdr', 'lmp', 'cmp', 'cc'}   # the recogniser sometimes writes a speaker label at a change of voice


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
            g, share = find(toks, heard, cursor, min(len(heard), cursor + 400 + 3 * len(toks)))
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
    (10 a second, normalised)."""
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
        return len(w) > 0 and float(w.max() - w.min()) < 0.4
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


def apply_fixes(mission, lines):
    """Hand corrections from listeners' reports, pipeline/transcript_fixes.json:
    {"11": [{"g": GET seconds, "from": "text as printed", "to": "corrected"}]};
    "speaker" in place of from/to puts a line to the right person; "delete": true
    (with "text") removes a line that's a scrap of another."""
    fixes = json.loads(FIXES.read_text()).get(mission, []) if FIXES.exists() else []
    done = 0
    for f in fixes:
        key = f.get('from', f.get('text', ''))
        match = (lambda t: t.strip() == key) if f.get('delete') else (lambda t: key in t)
        hit = [l for l in lines if abs(l['g'] - f['g']) <= 2 and match(l['t'])]
        if not hit:   # the line was re-timed (from the tapes): the nearest holding the text, within the hour
            near = sorted((abs(l['g'] - f['g']), k) for k, l in enumerate(lines) if abs(l['g'] - f['g']) <= 3600 and match(l['t']))
            hit = [lines[near[0][1]]] if near else []
        for l in hit:
            if f.get('delete'):
                l['t'] = ''
            elif 'speaker' in f:
                l['s'] = f['speaker']
            else:
                l['t'] = l['t'].replace(f['from'], f['to'])
        if hit:
            done += 1
        else:
            print(f"  fix not applied (text not found at GET {f['g']}): {f.get('from', f.get('text'))!r}")
    return done


def use_journal_text(mission, lines):
    """NASA's transcript is a scan read by OCR ("Cha_lie", "Ro6er"); the
    journal's transcript is the same conversation, corrected by hand. Where
    a line matches a journal line (same moment, mostly the same words), take
    the journal's wording and speaker. Returns how many lines changed."""
    journal = json.loads((ROOT / 'public' / 'transcripts' / f'apollo{mission}.json').read_text())
    jl = sorted((get_seconds(l['get']) if not l['get'].startswith('-') else -get_seconds(l['get'][1:]), l['speaker'], l['text'])
                for ls in journal.values() for l in ls if l.get('channel', 'air-to-ground') == 'air-to-ground')
    times = [x[0] for x in jl]
    used, changed = set(), 0
    for line in lines:
        toks = tokens(line['t'])
        if not toks:
            continue
        best, best_r = None, 0.6
        for j in range(bisect.bisect_left(times, line['g'] - 20), bisect.bisect_right(times, line['g'] + 20)):
            if j in used:
                continue
            # by word, and by letter (OCR breaks words: "Cha_lie" for "Charlie")
            r = max(difflib.SequenceMatcher(None, toks, tokens(jl[j][2]), autojunk=False).ratio(),
                    difflib.SequenceMatcher(None, ' '.join(toks), ' '.join(tokens(jl[j][2])), autojunk=False).ratio() - 0.1)
            if r > best_r:
                best, best_r = j, r
        if best is not None:
            used.add(best)
            if line['t'] != jl[best][2] or line['s'] != jl[best][1]:
                line['t'], line['s'] = jl[best][2], jl[best][1]
                changed += 1
    return changed


def trim_overlaps(segments):
    """Tapes were changed over with some overlap: play each tape to its end
    and pick up the next where it left off (trim the later piece's start)."""
    segments.sort(key=lambda s: s['get'])
    for a, b in zip(segments, segments[1:]):
        a_end = a['get'] + (a['to'] - a['from']) * a['rate']
        if b['get'] < a_end:
            cut = min(a_end - b['get'], (b['to'] - b['from']) * b['rate'])
            b['from'] = round(b['from'] + cut / b['rate'], 2)
            b['get'] = round(b['get'] + cut, 2)
    return [s for s in segments if s['to'] - s['from'] > 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    ap.add_argument('--journal-text', action='store_true',
                    help="take the Flight Journal's wording where a line matches (off: NASA's text, repaired from the tapes)")
    ap.add_argument('--cleaned', action='store_true',
                    help='play our cleaned copies (uploaded to <media>/audio/NN/<tape>.clean.m4a) instead of NASA\'s originals')
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    MISSION['n'] = m
    media = Path(args.media).expanduser()
    placement = json.loads((ROOT / 'pipeline' / 'tapes' / f'apollo{m}-placement.json').read_text())
    rows = [r for r in json.loads((ROOT / 'data' / 'nasa-transcripts' / f'as{m}-tec.json').read_text())
            if r['getSeconds'] > 0 or r['speaker'] not in ('MS', '?')]
    name = speaker_names(m, rows)

    segments, stats, tape_words, heard_at = [], {'anchored': 0, 'tried': 0}, {}, {}
    grams = {}   # three-word phrases of NASA's lines (timed ones) -> their GETs
    for r in rows:
        if r['getApprox']:
            continue
        toks = tokens(r['text'])
        for k in range(len(toks) - 2):
            grams.setdefault(' '.join(toks[k:k + 3]), []).append(r['getSeconds'])
    for tape, entry in sorted(placement.items()):
        asr = media / 'asr' / m / f'{tape}.json'
        if not asr.exists():
            continue
        words = [(w[0], w[1], w[2], (tokens(w[2]) or [''])[0]) for w in json.loads(asr.read_text())]
        starts = [w[0] for w in words]
        pieces = entry.get('pieces') or merge_pieces(spoken_pieces(words) + text_pieces(words, grams))
        if not pieces:
            continue
        tape_words[tape] = (words, starts)
        anchors = []
        for piece in pieces:
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
        if not entry.get('pieces'):   # (the stretches searched overlap: count each line once)
            stats['anchored'] -= len(anchors) - len(set(anchors))
            anchors = sorted(set(anchors))
        heard_at[tape] = sorted(t for t, _ in anchors)
        for p in pieces_from_anchors(anchors, entry['seconds'], starts, [w[1] for w in words]):
            segments.append({'tape': tape, **p})

    segments.sort(key=lambda s: s['get'])
    segments = trim_overlaps(segments)
    lines = [{'g': r['getSeconds'], 's': name(r), 't': r['text'], **({'a': 1} if r['getApprox'] else {})} for r in rows]
    untimed = time_untimed(lines, segments, tape_words)
    repaired = repair_ocr(lines, segments, tape_words)
    rebuilt = rebuild_from_tape(lines, segments, tape_words, vocabulary(tape_words)[0])
    fixed = use_journal_text(m, lines) if args.journal_text else 0
    # NASA's page headings read as if spoken ("11 AIR-TO-GROUND VOICE TRANSCRIPTION")
    lines = [l for l in lines if not re.search(r"AIR.{0,3}T.{0,4}.{0,3}G[RH]OUND|VOICE\s*T\S{0,3}[AJ]\S{0,3}S\S{0,2}R", l['t'])
             and not re.match(r"^\s*[1l]{2}\s+A\S{0,4}-", l['t'])   # "11 A_I_-TO-G][_OlJl_D VOICE ..."
             and re.search(r"[A-Za-z0-9]|\.\.\.|\*\*\*", l['t'])]   # (and lines that are only a stray mark: ")", "¢")
    out = ROOT / 'public' / 'timeline' / f'apollo{m}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    announcer, over, said = find_announcer(segments, lines, tape_words, heard_at)
    segments = trim_overlaps(segments)
    lines = sorted(lines + said, key=lambda l: l['g'])
    hand = apply_fixes(m, lines)
    lines = [l for l in lines if l['t']]   # (lines a hand fix deleted)
    unheard = mark_unheard(lines, segments, tape_words, media / 'envelopes' / 'tapes' / m)
    timeline = {'mission': m, 'segments': segments, 'lines': lines, 'announcer': announcer, 'over': over}
    if args.cleaned:   # (the site fills in {media}: its media storage address)
        timeline['audio'] = {'base': f'{{media}}/audio/{int(m)}', 'ext': '.clean.m4a'}
    out.write_text(json.dumps(timeline, separators=(',', ':')))
    covered = sum((s['to'] - s['from']) * s['rate'] for s in segments) / 3600
    print(f"{stats['anchored']} of {stats['tried']} lines found on the tapes; {len(segments)} segments covering {covered:.1f} h; "
          f"{len(lines)} lines ({repaired} words repaired from the tapes, {fixed} lines in the journal's wording, "
          f"{hand} hand fixes, {untimed} untimed lines timed from the tapes, {rebuilt} rebuilt from the tapes); announcer: {len(announcer)} stretches, {sum(b - a for a, b in announcer) / 60:.0f} min, over the crew in {len(over)} places; {unheard} lines not on the recording; written to {out}")


if __name__ == '__main__':
    main()
