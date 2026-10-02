"""Extract NASA's air-to-ground transcripts from the scanned PDFs on
https://www.nasa.gov/history/mission-transcripts-mercury-gemini-and-apollo/
and cross-check them against the journal transcripts the site already uses.

NASA's typed transcripts are public domain. Each row is
"DD HH MM SS  SPEAKER  text", with wrapped text on the following lines.

Two kinds of PDF:
  * Apollo 11 onward were digitised with a text layer that is nearly clean
    ("Pdf-It"), so words and their positions come straight from the PDF.
  * The early scans (Apollo 7-10) carry a garbled 1999 OCR layer, so those
    pages are rendered at 300 dpi and re-read with Tesseract.

Either way each page becomes a list of positioned words, and the columns
(time, speaker, text) are found from where the speaker codes sit.

    python3 scripts/nasa_transcripts.py extract as11-tec.pdf data/nasa-transcripts/as11-tec.json
    python3 scripts/nasa_transcripts.py merge as11-tec.pdf data/nasa-transcripts/as11-tec.json   # + Tesseract
    python3 scripts/nasa_transcripts.py check 11 data/nasa-transcripts/as11-tec.json report.md

`check` pairs every NASA line with the journal line at the same mission
time (within a few seconds) and scores how closely the words agree, then
writes a report with random samples of each kind of disagreement for a
person to spot-check.

Needs: pip install pymupdf; apt install tesseract-ocr (early PDFs only)
"""
import csv
import difflib
import io
import json
import random
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).parent.parent
SPEAKERS = ['CC', 'CDR', 'CMP', 'LMP', 'SC', 'MS', 'PAO', 'IWO', 'CT', 'HORNET', 'SWIM', 'MSFN']
# Typewriter digits that OCR commonly reads as letters
DIGIT_FIX = str.maketrans({'o': '0', 'O': '0', 'Q': '0', 'D': '0', 'l': '1', 'I': '1', 'i': '1',
                           '|': '1', 'k': '4', 'h': '4', 'A': '4', 'S': '5', 's': '5', 'B': '8',
                           'g': '9', 'Z': '2', 'z': '2', 'b': '6', 'G': '6', 'T': '7',
                           '[': '1', ']': '1', 't': '1', '(': '', ')': ''})
HEADER = re.compile(r'(?i)^\W*(\(?goss|tape|page|end of tape|\(?rev\b|air.to.ground)')
# Through a moonwalk NASA printed the command module's talk with Houston as
# its own blocks, on its own clock: "SEPARATE, SIMULTANEOUS COMMUNICATION(S)
# LINK IN USE BETWEEN CC AND CM" opens one, "... BETWEEN CC AND LM RESUMED"
# (when it's printed) closes it. The notes sometimes land inside a spoken
# line ("Stand COMMUNICATIONS by a second. LINK IN USE BETWEEN CC AND CM").
CM_LINK = ['COMMUNICATIONS', 'LINK', 'IN', 'USE', 'BETWEEN', 'CC', 'AND', 'CM']
CM_START = re.compile(r'\bLINK\s+BETWEEN\s+CC\s+AND\s+CM\s+ACTIVATED\b')
CM_END = re.compile(r'\bLM\s+RESUMED\b|\bLINK\s+BETWEEN\s+CC\s+AND\s+CM\s+SECURED\b')
CM_NOTES = re.compile(r'(?:\b(?:SEPARATE,\s+)?SIMULTANEOUS\s+)?\bCOMMUNICATIONS?\s+LINK\s+BETWEEN\s+CC\s+AND\s+CM\s+(?:ACTIVATED|SECURED)\b'
                      r'|(?:\b(?:OF\s+)?COMMUNICATIONS?\s+BETWEEN\s+)?(?:\bCC\s+)?(?:\bAND\s+)?\bLM\s+RESUMED\b(?:\s+SO\b|\s+\d{2,4}\b)?'
                      r'|\b(?:SEPARATE,\s+)?SIMULTANEOUS\b')
LUNAR_REV = re.compile(r'\s*\bBEGIN\s+LUNAR\s+REV\s+\d+\b')
CM_BANNER = re.compile(r'(?i:\bCOMMUNICATIONS?\s+(?:LINK\s+)?IN\s+USE\s+(?:LINK\s+)?BETWEEN\s+CC\s+AND\s+CM)\b'
                       r'|(?:\S+\s+)?\bLINK\s+IN\s+USE\s+\S+\s+CC\s+\S+\s+CM\b')   # (and a damaged one: "C0_CNiCATiONS LINK IN USE BET_EN CC A}_ CM")


def strip_notes(text):
    """A row's text without NASA's notes on the command module's link."""
    return re.sub(r'\s{2,}', ' ', LUNAR_REV.sub('', CM_NOTES.sub('', CM_BANNER.sub('', text)))).strip()
OCR_DPI = 300
SECOND_OCR_DPI = 200


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def closest_speaker(raw):
    """The speaker code a smudged token was meant to be, or '?' if unreadable."""
    # Apollo 12 on add the craft: "CDR-LM", "SC-CM" ("-I24" as misread)
    raw = re.split(r'-(?:[LIC1][M2N]|I24|L24|CM)\b|-', raw.upper())[0] if '-' in raw else raw
    raw = re.sub(r'[^A-Z0-9]', '', raw.upper()).replace('24', 'M').replace('I', 'L')
    if not raw:
        return '?'
    best = min(SPEAKERS, key=lambda s: edit_distance(raw, s))
    return best if edit_distance(raw, best) <= max(1, len(best) // 2) else '?'


def page_words(page, use_ocr, dpi=OCR_DPI):
    """[(x, y, text, confidence)] in PDF points."""
    if not use_ocr:
        return [(w[0], (w[1] + w[3]) / 2, w[4], 100.0) for w in page.get_text('words')]
    png = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).tobytes('png')
    out = subprocess.run(['tesseract', '-', '-', '--psm', '6', 'tsv'], input=png,
                         capture_output=True, check=True).stdout.decode()
    scale = 72 / dpi
    read = [r for r in csv.DictReader(io.StringIO(out), delimiter='\t', quoting=csv.QUOTE_NONE)
            if r['level'] == '5' and r['text'].strip()]
    # Every word takes the height of the line Tesseract read it in (the middle
    # one of that line's words): on a page scanned at a slight tilt (Apollo 8's)
    # a line's two ends differ by more than the lines are told apart by.
    heights = {}
    for r in read:
        heights.setdefault((r['block_num'], r['par_num'], r['line_num']), []).append(int(r['top']) + int(r['height']) / 2)
    middle = {k: sorted(v)[len(v) // 2] * scale for k, v in heights.items()}
    return [(int(r['left']) * scale, middle[(r['block_num'], r['par_num'], r['line_num'])], r['text'], float(r['conf'])) for r in read]


def group_lines(words):
    lines = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        if lines and abs(lines[-1][0] - w[1]) <= 4:
            lines[-1][1].append(w)
        else:
            lines.append([w[1], [w]])
    return [sorted(ws) for _, ws in lines]


def parse_hour(tokens):
    """The day and hour of a time printed without its minutes and seconds
    ("05 09 -- --", NASA's way through the moonwalks), in seconds, or None."""
    text = ' '.join(tokens)
    m = re.match(r'^\s*(\S\S)\s*(\S\S)\s*(?:[-.]{2,}\s*){1,2}$', text)
    if not m:
        return None
    d, h = (re.sub(r'\D', '', x.translate(DIGIT_FIX)) for x in m.groups())
    if len(d) != 2 or len(h) != 2 or int(h) > 23:
        return None
    return (int(d) * 24 + int(h)) * 3600


def get_pattern(tokens, read_by_ocr=False):
    """A time with smudged digits ("00 02 25 _1") as 8 characters, '?' for
    each unreadable digit, or None when it isn't a time at all. In a
    Tesseract reading a smudged digit comes out as any character ("3%" for
    34, "he" for 42): each one inside a group counts as unreadable."""
    if read_by_ocr:
        chars = ''.join(re.sub(r'[^0-9]', '?', t.strip('.,:;\'"`-').translate(DIGIT_FIX)) for t in tokens)
    else:
        chars = re.sub(r'[^0-9_]', '', ''.join(t.translate(DIGIT_FIX) for t in tokens)).replace('_', '?')
    return chars if len(chars) == 8 and 0 < chars.count('?') <= 3 else None


def fill_pattern(pattern, lo, hi):
    """The earliest time matching the pattern between lo and hi, or None."""
    import itertools
    holes = [i for i, ch in enumerate(pattern) if ch == '?']
    best = None
    for digits in itertools.product('0123456789', repeat=len(holes)):
        chars = list(pattern)
        for i, dg in zip(holes, digits):
            chars[i] = dg
        d, h, m, sec = (int(''.join(chars[i:i + 2])) for i in (0, 2, 4, 6))
        if h > 23 or m > 59 or sec > 59:
            continue
        t = ((d * 24 + h) * 60 + m) * 60 + sec
        if lo <= t <= hi and (best is None or t < best):
            best = t
    return best


def parse_get(tokens):
    digits = ''.join(t.translate(DIGIT_FIX) for t in tokens)
    digits = re.sub(r'\D', '', digits)
    if len(digits) != 8:
        return None
    d, h, m, s = (int(digits[i:i + 2]) for i in (0, 2, 4, 6))
    if h > 23 or m > 59 or s > 59:
        return None
    return ((d * 24 + h) * 60 + m) * 60 + s


def clean_text(text, vocab):
    # The typewriter's "1" was often read as "l": "Apollo ll", "option l".
    text = re.sub(r'\bll\b', '11', text)
    text = re.sub(r'(?<=\d)l\b|\bl(?=\d)', '1', text)

    # Rejoin words the typist broke across lines ("broadcast- ing"), but only
    # into words that appear elsewhere in the transcript, so dashes stay.
    def join(m):
        whole = m[1] + m[2]
        return whole if whole.lower().strip('.,?!;:') in vocab else m[0]
    return re.sub(r'\b([A-Za-z]+)- ([a-z]+\S*)', join, text)


def longest_forward_run(values):
    """Indexes of the longest non-decreasing subsequence, skipping None."""
    import bisect
    tails, tail_idx, prev = [], [], {}
    for i, v in enumerate(values):
        if v is None:
            continue
        k = bisect.bisect_right(tails, v)
        prev[i] = tail_idx[k - 1] if k else None
        if k == len(tails):
            tails.append(v)
            tail_idx.append(i)
        else:
            tails[k] = v
            tail_idx[k] = i
    keep, i = set(), tail_idx[-1] if tail_idx else None
    while i is not None:
        keep.add(i)
        i = prev[i]
    return keep


_ocr_doc = {}


def _ocr_page(job):
    """One page's words by Tesseract (a worker process: it keeps the PDF open)."""
    pdf_path, pno, dpi = job
    if pdf_path not in _ocr_doc:
        _ocr_doc[pdf_path] = pymupdf.open(pdf_path)
    return page_words(_ocr_doc[pdf_path][pno], True, dpi)


TAPE_HEAD = re.compile(r'(?i)^\W*tape\W+(\S+)')


def tape_letter(lines):
    """'A' or 'B' from a page's heading "Tape 80B/1" (Apollo 17: from
    undocking to the rendezvous each tape was transcribed as two, A the lunar
    module's link and B the command module's), or None."""
    for ws in lines[:6]:
        m = TAPE_HEAD.match(' '.join(w[2] for w in ws))
        if m:
            core = m.group(1).split('/')[0]
            if len(core) >= 2 and core[-1] in 'AB' and re.search(r'[0-9lIiOo]', core[:-1]):
                return core[-1]
            return None
    return None


def needs_ocr(doc):
    """The early scans (Apollo 7-10) carry a garbled 1999 text layer: read afresh."""
    return 'Acrobat Capture' in (doc.metadata.get('creator') or '')


def extract(pdf_path, force_ocr=False, pages=None, dpi=OCR_DPI):
    doc = pymupdf.open(pdf_path)
    use_ocr = force_ocr or needs_ocr(doc)
    rows, letters = [], {}
    page_list = list(pages if pages is not None else range(doc.page_count))
    read = {}
    if use_ocr and len(page_list) > 8:   # Tesseract page by page, on every core
        import os
        from concurrent.futures import ProcessPoolExecutor
        os.environ.setdefault('OMP_THREAD_LIMIT', '1')
        with ProcessPoolExecutor(max(1, (os.cpu_count() or 4) - 2)) as pool:
            read = dict(zip(page_list, pool.map(_ocr_page, [(str(pdf_path), n, dpi) for n in page_list], chunksize=4)))
    for pno in page_list:
        lines = group_lines(read[pno] if pno in read else page_words(doc[pno], use_ocr, dpi))
        letters[pno + 1] = tape_letter(lines)
        # The speaker column is where exact speaker codes line up.
        spk_x = sorted(w[0] for ws in lines for w in ws if w[2].strip('.:') in SPEAKERS and w[0] > 100)
        if not spk_x:
            continue
        col = spk_x[len(spk_x) // 2]
        firsts = sorted(w[0] for ws in lines for w in ws if w[0] > col + 20)
        text_x = min(firsts) if firsts else col + 40
        for ws in lines:
            if use_ocr:
                # specks on the old scans are read as stray marks: left of the text a word has a letter
                # or digit in it, and a lone "|" anywhere is the page's edge
                ws = [w for w in ws if w[2] != '|' and (w[0] >= text_x - 12 or re.search(r'[A-Za-z0-9]', w[2]))]
                if not ws:
                    continue
            if HEADER.match(' '.join(w[2] for w in ws)):
                continue
            spk = [w for w in ws if abs(w[0] - col) <= 14]
            text = [w for w in ws if w[0] >= text_x - 12]
            if spk and spk[0][2].startswith('(') and rows:
                # "(EAGLE)" / "(COLUMBIA)" under a speaker code names the call
                # sign, which identifies the CMP when the code itself is smudged.
                if rows[-1]['speaker'] == '?' and 'COLUMBIA' in spk[0][2].upper():
                    rows[-1]['speaker'] = 'CMP'
                rows[-1]['words'] += text
            elif spk:
                stamp = [w[2] for w in ws if w[0] < col - 14]
                while use_ocr and len(stamp) > 1 and len(re.sub(r'\D', '', ''.join(t.translate(DIGIT_FIX) for t in stamp))) > 8:
                    stamp = stamp[1:]   # (a punch hole or the page's edge read as a character before the time)
                rows.append({'getSeconds': parse_get(stamp), 'hour': parse_hour(stamp), 'pattern': get_pattern(stamp, use_ocr),
                             'speaker': closest_speaker(spk[0][2]),
                             'words': text, 'page': pno + 1})
            elif rows and text and (ws[0][0] >= text_x - 12 or use_ocr and len(ws) - len(text) <= 2
                                    and all(len(w[2]) <= 3 for w in ws if w[0] < text_x - 12)):
                rows[-1]['words'] += text   # (a line carried on; on the old scans, past a speck or two read as "C)", "7:")
    streams = cm_link_streams(rows)
    if not any(streams):
        streams = tape_letter_streams(rows, letters)
    resolve_times(rows, streams)
    vocab = {w[2].lower().strip('.,?!;:') for r in rows for w in r['words']}
    out = []
    for r, stream in zip(rows, streams):
        text = clean_text(' '.join(w[2] for w in r['words']), vocab)
        text = strip_notes(text)
        if not text:
            continue
        out.append({'getSeconds': r['getSeconds'], 'getApprox': r['getApprox'], 'hourOnly': r['hour'] is not None, 'speaker': r['speaker'],
                    'text': text, 'unsure': [w[2] for w in r['words'] if w[3] < 80], 'page': r['page'],
                    **({'loop': 'CM'} if stream else {})})
    return out


def _is_word(read, word):
    read = re.sub(r'[^A-Za-z]', '', read)
    if not read or sum(ch.isupper() for ch in read) < 0.6 * len(read):   # (typed in capitals: "LiNK" is a misread)
        return False
    read = read.upper()
    return read == word or (len(word) >= 5 and edit_distance(read, word) <= 2) or (word == 'COMMUNICATIONS' and read == 'COMMUNICATION')


def strip_cm_link(words):
    """The words of a row without NASA's "COMMUNICATIONS LINK IN USE BETWEEN
    CC AND CM" note, and whether it held the note (all eight words, in order)."""
    at, k = [], 0
    for i, w in enumerate(words):
        if k < len(CM_LINK) and _is_word(w[2], CM_LINK[k]):
            at.append(i)
            k += 1
    if k < len(CM_LINK):
        # a row that's the note alone, a word or two out of place ("COMMUNICATIONS IN USE LINK BETWEEN")
        at = [i for i, w in enumerate(words) if any(_is_word(w[2], c) for c in CM_LINK)]
        if len(at) < 6 or len(words) > len(at) + 2:
            return words, False
        return [], True   # (the note alone, and a word of it too damaged to know: "CON[_3NICATIONS")
    return [w for i, w in enumerate(words) if i not in set(at)], True


def cm_link_streams(rows):
    """Which rows are the command module's separate block (1, 2, ... for
    each block; 0 for the rest). A block runs from NASA's note to "... AND LM
    RESUMED", or else to where the crew on the Moon talk again (two CDR/LMP
    rows close together: only the CMP and CapCom are on that link), or the
    next note. The note itself is taken out of the row it's in."""
    streams, block, inside = [0] * len(rows), 0, False
    for i, r in enumerate(rows):
        r['words'], note = strip_cm_link(r['words'])
        text = ' '.join(w[2] for w in r['words'])
        if note or CM_START.search(text):
            block, inside = block + 1, True
        elif inside and CM_END.search(text):
            inside = False
        elif inside and r['speaker'] in ('CDR', 'LMP') and any(x['speaker'] in ('CDR', 'LMP') for x in rows[i + 1:i + 4]):
            inside = False
        if inside:
            streams[i] = block
    return streams


def tape_letter_streams(rows, letters):
    """The command module's blocks where NASA printed no note of them but
    transcribed each tape as two (Apollo 17: "Tape 80A", the lunar module's
    link, then "Tape 80B", the command module's, over the same hours): 1, 2,
    ... for the rows of each run of B pages, 0 for the rest. A heading read
    as a letter counts only with another lettered page within two pages of it
    (a lone "2B/3" is 28/3 misread). Between the first and last lettered
    pages, a page whose letter can't be read goes by who speaks on it (the
    CMP: the command module's; the CDR or LMP: the lunar module's), or else
    with the page before it."""
    known = sorted(p for p, x in letters.items() if x)
    sure = [p for p in known if any(q != p and abs(q - p) <= 2 for q in known)]
    if len(sure) < 20:
        return [0] * len(rows)
    first, last = sure[0], sure[-1]
    speakers = {}
    for r in rows:
        speakers.setdefault(r['page'], []).append(r['speaker'])
    page_letter, prev = {}, 'A'
    for p in range(first, last + 1):
        x = letters.get(p) if p in sure else None
        if not x:
            who = speakers.get(p, [])
            cm, lm = who.count('CMP'), who.count('CDR') + who.count('LMP')
            x = 'B' if cm > lm else 'A' if lm > cm else prev
        page_letter[p] = prev = x
    streams, block, before = [0] * len(rows), 0, 'A'
    for i, r in enumerate(rows):
        x = page_letter.get(r['page'], 'A')
        if x == 'B' and before != 'B':
            block += 1
        before = x
        if x == 'B':
            streams[i] = block
    return streams


BLOCK_SLACK = 6 * 3600   # how far a command-module block's times may lie from the main transcript's on either side of it


def resolve_times(rows, streams):
    """Each row's mission time, stream by stream (the main transcript, and
    each of the command module's blocks on its own clock). The typed times
    only go forward, so the rows whose times form the longest non-decreasing
    run are trusted; the rest (misread or unreadable) take the time of the
    trusted row before them. A row with only its day and hour starts no
    earlier than that hour. A time with a smudged digit or two takes the
    one value that fits between its trusted neighbours."""
    for s in sorted(set(streams)):
        idx = [i for i, x in enumerate(streams) if x == s]
        part = [rows[i] for i in idx]
        values = [r['getSeconds'] for r in part]
        if s:   # a block's times lie near the main transcript's around it: one far off is a misread ("02 17 59 52" for day 04)
            lo = next((rows[i]['getSeconds'] for i in range(idx[0] - 1, -1, -1) if not streams[i]), None)
            hi = next((rows[i]['getSeconds'] for i in range(idx[-1] + 1, len(rows)) if not streams[i] and not rows[i]['getApprox']), None)
            values = [None if v is None or (lo is not None and v < lo - BLOCK_SLACK) or (hi is not None and v > hi + BLOCK_SLACK)
                      else v for v in values]
        trusted = longest_forward_run(values)
        nxt, following = None, [None] * len(part)
        for i in range(len(part) - 1, -1, -1):
            following[i] = nxt
            if i in trusted:
                nxt = part[i]['getSeconds']
        last = 0
        if s:   # a block starts no earlier than the main transcript's last trusted time before its first trusted one
            first = min((part[i]['getSeconds'] for i in trusted), default=None)
            last = 0 if first is None else first
        for i, r in enumerate(part):
            r['getApprox'] = i not in trusted
            if r['getApprox']:
                filled = fill_pattern(r['pattern'], last, following[i] if following[i] is not None else 10 ** 7) if r['pattern'] else None
                r['getSeconds'], r['getApprox'] = (filled, False) if filled is not None else (max(last, r['hour'] or 0), True)
            last = r['getSeconds']


DAMAGE = re.compile(r"[^A-Za-z0-9'.,?!;:()/&\-]|[a-z][0-9]|[0-9][a-z]{2}|[a-z][,:;][a-z]|[A-Za-z][éèàù]")


SHORT_WORDS = set('a i am an as at be by do go he if in is it me my no of oh ok on or so to up us we ye'.split())


def _word_score(word, vocab):
    """How trustworthy a word reads: 2 a dictionary or oft-seen word, 1 clean
    but unfamiliar, 0 visibly damaged."""
    core = word.strip('.,?!;:"()')
    if not core or DAMAGE.search(core):
        return 0
    if re.fullmatch(r"[\d.,:/-]+", core):
        return 2
    real = core.lower() in vocab and (len(core) >= 3 or core.lower() in SHORT_WORDS)
    return 2 if real or (core.isupper() and len(core) >= 2) else 1


def _better(new, old, common, vocab):
    """Whether Tesseract's word should replace the embedded text's: the old
    one reads worse, and the new one is a word these transcripts use again
    and again (a rarer one, "Yates" or "yodates", is more likely a misreading;
    those are left to the repairs from the tapes)."""
    if _word_score(old, vocab) == 2:
        return False
    if _word_score(new, common) == 2:
        return True
    # a dictionary word that looks like what's readable of the damaged one ("readin&s": readings)
    seen = re.sub(r'[^a-z]', '', old.lower())
    return (_word_score(new, vocab) == 2 and len(seen) >= 3
            and difflib.SequenceMatcher(None, seen, re.sub(r'[^a-z]', '', new.lower())).ratio() >= 0.75)


def merge_readings(old, new, vocab, nearby='', common=None):
    """Two readings of one line (the PDF's embedded text, and Tesseract's)
    merged word by word: where they disagree, the reading that scores
    better as a word wins; on a tie the embedded text stays.

    Words only Tesseract saw are added only as a run of 3+ real words that
    isn't in the lines around (`nearby`: Tesseract sometimes splits the
    page into lines differently, and a neighbour's words bleed in) and
    doesn't repeat what this line already says."""
    common = common if common is not None else vocab
    a, b = old.split(), new.split()
    near = ' ' + ' '.join(re.sub(r'[^a-z0-9 ]', '', w.lower()) for w in nearby.split()) + ' '
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [w.lower() for w in a], [w.lower() for w in b], autojunk=False).get_opcodes():
        if op == 'equal':
            out += a[i1:i2]
        elif op == 'replace' and i2 - i1 == j2 - j1:
            out += [y if _better(y, x, common, vocab) else x for x, y in zip(a[i1:i2], b[j1:j2])]
        elif op == 'replace':   # stretches of different lengths: Tesseract's only where every old word is damaged
            old_all_bad = all(_word_score(w, vocab) == 0 for w in a[i1:i2])
            new_all_good = all(_word_score(w, common) == 2 for w in b[j1:j2])
            out += b[j1:j2] if old_all_bad and new_all_good and abs((j2 - j1) - (i2 - i1)) <= 2 else a[i1:i2]
        elif op == 'delete':
            out += [w for w in a[i1:i2] if _word_score(w, vocab) > 0]   # a scrap only the old reading has
        else:   # 'insert': only Tesseract saw these
            run = b[j1:j2]
            plain = ' '.join(re.sub(r'[^a-z0-9]', '', w.lower()) for w in run)
            own = {re.sub(r'[^a-z0-9]', '', w.lower()) for w in a}
            if (len(run) >= 3 and all(_word_score(w, common) == 2 for w in run) and f' {plain} ' not in near
                    and sum(re.sub(r'[^a-z0-9]', '', w.lower()) in own for w in run) * 2 < len(run)):
                out += run
    return ' '.join(out)


def extract_merged(pdf_path, pages=None, cache=None):
    """Both readings of the scan (embedded text layer and a fresh Tesseract
    pass), lined up row by row and merged word by word. Times and speakers
    come from whichever reading has them readable. With `cache` (a path
    prefix), each reading is saved and reused, so re-merging is quick."""
    def reading(name, **kw):
        path = Path(f'{cache}.{name}.json') if cache else None
        if path and path.exists():
            return json.loads(path.read_text())
        rows = extract(pdf_path, pages=pages, **kw)
        if path:
            path.write_text(json.dumps(rows))
        return rows
    old = reading('embedded')
    # (an early scan's first reading is Tesseract's already: its second is at another resolution,
    # where Tesseract misreads different words and digits)
    new = reading('tesseract', force_ocr=True, **({'dpi': SECOND_OCR_DPI} if needs_ocr(pymupdf.open(pdf_path)) else {}))
    words = [w.lower().strip('.,?!;:"()') for r in old + new for w in r['text'].split()]
    from collections import Counter
    seen = Counter(words)
    common = {w for w, n in seen.items() if n >= 3 and not DAMAGE.search(w)}   # words these transcripts use again and again
    vocab = set(common)
    dict_path = Path('/usr/share/dict/words')
    if dict_path.exists():
        vocab |= {w.lower() for w in dict_path.read_text(errors='ignore').split()}
    key = lambda t: re.sub(r'[^a-z]', '', t.lower())[:60]
    pairs = difflib.SequenceMatcher(None, [key(r['text']) for r in old], [key(r['text']) for r in new], autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in pairs.get_opcodes():
        if op in ('equal', 'replace') and i2 - i1 == j2 - j1:
            for k, (r, q) in enumerate(zip(old[i1:i2], new[j1:j2])):
                i = i1 + k
                nearby = ' '.join(x['text'] for x in old[max(0, i - 2):i] + old[i + 1:i + 3])
                m = dict(r)
                m['text'] = strip_notes(merge_readings(r['text'], q['text'], vocab, nearby, common))
                if r['getApprox'] and not q['getApprox']:
                    m['getSeconds'], m['getApprox'] = q['getSeconds'], False
                if r['speaker'] == '?' and q['speaker'] != '?':
                    m['speaker'] = q['speaker']
                out.append(m)
        else:
            out += old[i1:i2]   # rows the readings split differently: keep the embedded reading
    out = [r for r in out if r['text']]
    # a row neither reading could time follows the row before it (in its own
    # stream), now the second reading may have timed that one later
    last = {}
    for r in out:
        k = r.get('loop', '')
        if r['getApprox']:
            r['getSeconds'] = max(r['getSeconds'], last.get(k, 0))
        last[k] = r['getSeconds']
    return out


def fmt_get(s):
    return f'{s // 3600:03d}:{s % 3600 // 60:02d}:{s % 60:02d}'


def first_line(text):
    # Some journal lines run on into the next speaker's ("... 111:22:59 Aldrin: ...")
    return re.split(r'\s\d{2,3}:\d\d:\d\d \w', text)[0]


def words_of(text):
    text = first_line(text)
    text = re.sub(r'\[[^\]]*\]?|\([^)]*\)', ' ', text.lower()).replace('rog.', 'roger.')
    return re.findall(r"[a-z0-9']+", text.replace(',', ''))


def check(mission_id, rows_path, report_path, window=4):
    nasa = json.loads(Path(rows_path).read_text())
    journal = []
    for lines in json.loads((ROOT / 'public' / 'transcripts' / f'apollo{mission_id}.json').read_text()).values():
        for ln in lines:
            m = re.match(r'(\d+):(\d\d):(\d\d)', ln.get('get') or '')
            if m and ln.get('channel', 'air-to-ground') == 'air-to-ground':
                g = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
                journal.append((g, ln['speaker'], ln['text']))
    journal.sort()
    by_sec = {}
    for j in journal:
        by_sec.setdefault(j[0], []).append(j)
    lo, hi = journal[0][0], journal[-1][0]

    results = []
    for r in nasa:
        if r['getApprox'] or not lo <= r['getSeconds'] <= hi:
            continue
        a = words_of(r['text'])
        best = None
        for dt in range(-window, window + 1):
            for j in by_sec.get(r['getSeconds'] + dt, []):
                b = words_of(j[2])
                ratio = difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0
                if not best or ratio > best[0]:
                    best = (ratio, j)
        results.append((r, best))

    paired = [(r, b) for r, b in results if b]
    agree = [x for x in paired if x[1][0] >= 0.9]
    minor = [x for x in paired if 0.6 <= x[1][0] < 0.9]
    major = [x for x in paired if x[1][0] < 0.6]
    only_nasa = [r for r, b in results if not b]
    words_total = sum(len(words_of(r['text'])) for r, _ in paired)
    words_same = sum(sum(m.size for m in difflib.SequenceMatcher(None, words_of(r['text']), words_of(b[1][2])).get_matching_blocks())
                     for r, b in paired)

    def sample(items, n=15):
        random.seed(7)
        return random.sample(items, min(n, len(items)))

    def show(r, b):
        return (f'- **GET {fmt_get(r["getSeconds"])}** (NASA p. {r["page"]}, match {b[0]:.0%})\n'
                f'  - NASA ({r["speaker"]}): {r["text"]}\n'
                f'  - Journal ({b[1][1]}): {first_line(b[1][2])[:400]}\n')

    crew = re.search(rf"id: '{mission_id}'.*?crew: \[([^\]]*)\]", (ROOT / 'src' / 'data' / 'missions.js').read_text(), re.S)
    names = [n.strip(" '").split()[-1] for n in crew[1].split(',')] if crew else []
    roles = dict(zip(['CDR', 'CMP', 'LMP'], names))

    def same_speaker(code, name):
        if code in roles:
            return roles[code] == name
        if code == 'CC':
            return name not in names
        return None
    judged = [same_speaker(r['speaker'], b[1][1]) for r, b in agree + minor]
    judged = [j for j in judged if j is not None]
    wrong_spk = [(r, b) for r, b in agree + minor if same_speaker(r['speaker'], b[1][1]) is False]

    rep = [f'# Apollo {mission_id}: NASA transcript vs journal transcript\n',
           f'NASA rows extracted: {len(nasa):,} ({sum(r["getApprox"] for r in nasa):,} with an unreadable or out-of-order time).',
           f'Journal air-to-ground lines: {len(journal):,}, covering GET {fmt_get(lo)}-{fmt_get(hi)}.\n',
           f'Of {len(results):,} NASA rows in that span, {len(paired):,} have a journal line within {window} s:',
           f'- {len(agree):,} agree (90%+ of words match)',
           f'- {len(minor):,} differ a little (60-90%)',
           f'- {len(major):,} differ a lot (under 60%)',
           f'- {len(only_nasa):,} NASA rows have no journal line nearby (the journal only covers the clips on this site)\n',
           f'Word-level agreement across paired rows: {words_same / max(words_total, 1):.1%}.\n',
           f'Speaker: on rows whose words match (60%+), NASA and the journal name the same speaker '
           f'{sum(judged) / max(len(judged), 1):.1%} of the time (CDR/CMP/LMP = {", ".join(names)}).\n',
           '## Differ a little (random sample)\n', *[show(r, b) for r, b in sample(minor)],
           '\n## Differ a lot (random sample)\n', *[show(r, b) for r, b in sample(major)],
           '\n## Different speaker (random sample)\n', *[show(r, b) for r, b in sample(wrong_spk, 10)],
           '\n## Agree (random sample)\n', *[show(r, b) for r, b in sample(agree, 8)]]
    Path(report_path).write_text('\n'.join(rep))
    print('\n'.join(rep[:10]))


if __name__ == '__main__':
    if sys.argv[1] == 'extract':
        rows = extract(sys.argv[2])
        Path(sys.argv[3]).parent.mkdir(parents=True, exist_ok=True)
        Path(sys.argv[3]).write_text(json.dumps(rows, indent=0))
        print(len(rows), 'rows,', sum(r['getApprox'] for r in rows), 'with approximate time')
    elif sys.argv[1] == 'merge':   # embedded text + Tesseract, merged word by word
        rows = extract_merged(sys.argv[2], cache=sys.argv[3].removesuffix('.json'))
        Path(sys.argv[3]).parent.mkdir(parents=True, exist_ok=True)
        Path(sys.argv[3]).write_text(json.dumps(rows, indent=0))
        print(f'{len(rows)} rows, {sum(r["getApprox"] for r in rows)} with approximate time')
    elif sys.argv[1] == 'check':
        check(sys.argv[2], sys.argv[3], sys.argv[4])
