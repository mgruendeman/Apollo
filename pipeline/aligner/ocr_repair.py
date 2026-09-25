"""Repairing OCR damage in NASA's typed transcript, from dictionaries and from what the tapes say."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np
from .common import ROOT, tokens
from .placement import find

LABELS = {'capcom', 'sc', 'cdr', 'lmp', 'cmp', 'cc'}   # the recogniser sometimes writes a speaker label at a change of voice

# NASA's text came through OCR: "We'11" for "We'll", "Ro6er", "Cha_lie", stray ")".
FIXES = ROOT / 'pipeline' / 'transcript_fixes.json'


DICT = Path('/usr/share/dict/words')
CONFUSED = {'6': 'gb', '0': 'o', '1': 'li', '5': 's', '8': 'b', 'c': 'oe', 'e': 'c', 'o': 'c', '_': 'abcdefghijklmnopqrstuvwxyz', ';': 't',
            'i': 'l', 'l': 'i', 't': 'c', 'E': 'GH', '(': 'G', '!': 'l', '*': 'r', '$': 's', '%': 'r', ']': 'l', '}': 'h',
            '?': 'h', "'": 'lnh', '¢': 'vc', 'k': 'b', 'r': 'n', 's': 'a'}
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
DIGIT_LOOKS = {'1': '[1!il|It]', '2': '[2Zz&]', '4': '[4hA]', '5': '[5sS]', '6': '[6bG]', '7': '[7T]', '0': '[0oO]'}


def _place(word):
    """The station or callsign a damaged word stands for, if it's close."""
    letters = re.sub(r"[^a-z]", '', word.lower())
    if len(letters) < 4:
        return None
    places = PLACES + CALLSIGNS.get(MISSION['n'], [])
    # An underscore is a letter the scan lost ("Tar_n_ri_e"): it matches any
    # letter, so a name with a few gaps still scores as itself.
    gaps = re.sub(r"[^a-z_]", '', word.lower())
    def score(p):
        plain = difflib.SequenceMatcher(None, letters, p.lower()).ratio()
        if '_' in gaps and len(gaps) == len(p):   # (the gap rule can only help, never lower a score)
            return max(plain, sum(1 for a, b in zip(gaps, p.lower()) if a == b or a == '_') / len(p))
        return plain
    best = max(places, key=score)
    ratio = score(best)
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
    text = re.sub(r"^(?!\.\.\.)[.,;:'_\s]+(?=[A-Z])", '', text)            # ".., We're", ".. _ Houston"
    text = re.sub(r",\s*$", '.', text)                                     # a line ending "Over,"
    text = re.sub(r"(?<=\s)_(?=\d)|(?<=\d)_(?=\s|$)", '', text)            # "_103.0"
    n = str(int(MISSION['n']))                                                  # the mission's number, as OCR misreads it
    looks = ''.join(DIGIT_LOOKS.get(ch, ch) for ch in n)
    text = re.sub(r"\bApollo\s+" + looks + r"(?![A-Za-z0-9])", 'Apollo ' + n, text)   # "Apollo !1", "Apollo lZ", "Apollo l&,"
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
    text = re.sub(r"\s+Tape\s+\d+/\d+\s*$", '', text)                          # a page heading: "Tape 1/11"
    text = re.sub(r"\s+-?\d?\s*NOTE\s*$", '', text)                            # "-3 NOTE": the start of a page note
    text = re.sub(r"(?<=[.?!])\s+(?:[b-hj-z]|i(?:\s*-\))?)\s*$", '', text)       # a stray letter after the last sentence: "Copy. i"
    if text.count('"') % 2 == 1:
        text = re.sub(r'(?<=\w)"(?=\s)', '', text, count=1)                   # an unmatched quote: 'builder number" going'
    text = re.sub(r"\bPS(\d)\b", r"P5\1", text)                                 # "PS1": program P51
    text = re.sub(r"\bAil\b", 'All', text)
    text = re.sub(r"\bSim\)\s*lex\b", 'Simplex', text)                      # "Sim) lex Alfa"                                    # "Ail we have": nobody here says "ail"
    text = re.sub(r"\b(\d+)h(?=[\s.,;]|$)", r"\g<1>4", text)                     # "0h", "2351h": a misread 4
    text = re.sub(r"\b(\d+)h\.(\d)", r"\g<1>4.\2", text)                        # "2h.1"
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
    text = re.sub(r"\s+[PF][a-z_?]{2}e\s+\d{2,4}\s*$", '', text)                 # "Pase 309", "Fage 12"
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


