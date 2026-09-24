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
    python3 scripts/nasa_transcripts.py html URL data/nasa-transcripts/as11-tec.json

`html` reads NASA's clean digital typing of a transcript, where there is one
(Apollo 11's Technical Air-to-Ground, on NASA's history site:
https://www.nasa.gov/wp-content/uploads/static/history//alsj/a11/a11transcript_tec.html),
in place of reading the scanned PDF.
    python3 scripts/nasa_transcripts.py check 11 data/nasa-transcripts/as11-tec.json report.md

`check` pairs every NASA line with the journal line at the same mission
time (within a few seconds) and scores how closely the words agree, then
writes a report with random samples of each kind of disagreement for a
person to spot-check.

Needs, for the PDFs: pip install pymupdf; apt install tesseract-ocr (early PDFs only)
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


ROOT = Path(__file__).parent.parent
SPEAKERS = ['CC', 'CDR', 'CMP', 'LMP', 'SC', 'MS', 'PAO', 'IWO', 'CT', 'HORNET', 'SWIM', 'MSFN']
# Typewriter digits that OCR commonly reads as letters
DIGIT_FIX = str.maketrans({'o': '0', 'O': '0', 'Q': '0', 'D': '0', 'l': '1', 'I': '1', 'i': '1',
                           '|': '1', 'k': '4', 'h': '4', 'A': '4', 'S': '5', 's': '5', 'B': '8',
                           'g': '9', 'Z': '2', 'z': '2', 'b': '6', 'G': '6', 'T': '7',
                           '[': '1', ']': '1', 't': '1', '(': '', ')': ''})
HEADER = re.compile(r'(?i)^\W*(\(?goss|tape|page|end of tape|\(?rev\b|air.to.ground)')
OCR_DPI = 300


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
    raw = re.sub(r'[^A-Z0-9]', '', raw.upper()).replace('24', 'M').replace('I', 'L')
    if not raw:
        return '?'
    best = min(SPEAKERS, key=lambda s: edit_distance(raw, s))
    return best if edit_distance(raw, best) <= max(1, len(best) // 2) else '?'


def page_words(page, use_ocr):
    """[(x, y, text, confidence)] in PDF points."""
    if not use_ocr:
        return [(w[0], (w[1] + w[3]) / 2, w[4], 100.0) for w in page.get_text('words')]
    import pymupdf
    png = page.get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csGRAY).tobytes('png')
    out = subprocess.run(['tesseract', '-', '-', '--psm', '6', 'tsv'], input=png,
                         capture_output=True, check=True).stdout.decode()
    scale = 72 / OCR_DPI
    words = []
    for r in csv.DictReader(io.StringIO(out), delimiter='\t', quoting=csv.QUOTE_NONE):
        if r['level'] == '5' and r['text'].strip():
            y = (int(r['top']) + int(r['height']) / 2) * scale
            words.append((int(r['left']) * scale, y, r['text'], float(r['conf'])))
    return words


def group_lines(words):
    lines = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        if lines and abs(lines[-1][0] - w[1]) <= 4:
            lines[-1][1].append(w)
        else:
            lines.append([w[1], [w]])
    return [sorted(ws) for _, ws in lines]


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


def extract(pdf_path):
    import pymupdf   # (only the PDFs need it)
    doc = pymupdf.open(pdf_path)
    use_ocr = 'Acrobat Capture' in (doc.metadata.get('creator') or '')
    rows = []
    for pno in range(doc.page_count):
        lines = group_lines(page_words(doc[pno], use_ocr))
        # The speaker column is where exact speaker codes line up.
        spk_x = sorted(w[0] for ws in lines for w in ws if w[2].strip('.:') in SPEAKERS and w[0] > 100)
        if not spk_x:
            continue
        col = spk_x[len(spk_x) // 2]
        firsts = sorted(w[0] for ws in lines for w in ws if w[0] > col + 20)
        text_x = min(firsts) if firsts else col + 40
        for ws in lines:
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
                get = parse_get([w[2] for w in ws if w[0] < col - 14])
                rows.append({'getSeconds': get, 'speaker': closest_speaker(spk[0][2]),
                             'words': text, 'page': pno + 1})
            elif rows and text and ws[0][0] >= text_x - 12:
                rows[-1]['words'] += text
    # The typed times only go forward, so the rows whose times form the longest
    # non-decreasing run are trusted; the rest (misread or unreadable) take
    # the time of the trusted row before them.
    trusted = longest_forward_run([r['getSeconds'] for r in rows])
    last = 0
    for i, r in enumerate(rows):
        r['getApprox'] = i not in trusted
        if r['getApprox']:
            r['getSeconds'] = last
        last = r['getSeconds']
    vocab = {w[2].lower().strip('.,?!;:') for r in rows for w in r['words']}
    out = []
    for r in rows:
        text = clean_text(' '.join(w[2] for w in r['words']), vocab)
        if not text:
            continue
        out.append({'getSeconds': r['getSeconds'], 'getApprox': r['getApprox'], 'speaker': r['speaker'],
                    'text': text, 'unsure': [w[2] for w in r['words'] if w[3] < 80], 'page': r['page']})
    return out


def extract_html(source):
    """Rows from NASA's digital typing of a transcript: each line is
    "DD HH MM SS <font>SPEAKER</font> (CRAFT)<br> text <br><br>"; tape and page
    headings and "BEGIN LUNAR REV" markers in between are skipped."""
    import html as htmllib
    import urllib.request
    if re.match(r'https?://', source):
        req = urllib.request.Request(source, headers={'User-Agent': 'apollo-pipeline'})
        raw = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'ignore')
    else:
        raw = Path(source).read_text(errors='ignore')
    rows = []
    entry = re.compile(r'(\d\d) (\d\d) (\d\d) (\d\d)\s*<font[^>]*>\s*([A-Z][A-Z0-9 ]*?)\s*</font>\s*(?:\(([A-Z ]+)\))?\s*<br>(.*?)(?:<br>\s*<br>|(?=\d\d \d\d \d\d \d\d\s*<font))',
                       re.S | re.I)
    for m in entry.finditer(raw):
        d, h, mi, sec, speaker, craft, body = m.groups()   # craft: (COLUMBIA), (EAGLE), (TRANQ)
        text = htmllib.unescape(re.sub(r'<[^>]+>', ' ', body))
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            continue
        rows.append({'getSeconds': int(d) * 86400 + int(h) * 3600 + int(mi) * 60 + int(sec), 'getApprox': False,
                     'speaker': re.sub(r'\s+\d+$', '', speaker.strip()).replace('NIX0N', 'NIXON'), 'text': text,
                     'unsure': [], 'page': None, 'typed': True})
    # A mistyped time (a wrong digit: 124 hours for 76) disagrees with the
    # lines both sides of it, which agree with each other: take the line
    # before's time and flag it approximate.
    # (or a short run of them, up to 4 lines)
    for i in range(1, len(rows) - 1):
        a = rows[i - 1]['getSeconds']
        for j in range(i, min(i + 4, len(rows) - 1)):
            if abs(rows[j]['getSeconds'] - a) <= 600:
                break
            if abs(rows[j + 1]['getSeconds'] - a) <= 600:
                for k in range(i, j + 1):
                    rows[k]['getSeconds'], rows[k]['getApprox'] = a, True
                break
    return rows


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
    elif sys.argv[1] == 'html':
        rows = extract_html(sys.argv[2])
        Path(sys.argv[3]).parent.mkdir(parents=True, exist_ok=True)
        Path(sys.argv[3]).write_text(json.dumps(rows, indent=0))
        print(f'{len(rows)} lines')
    elif sys.argv[1] == 'check':
        check(sys.argv[2], sys.argv[3], sys.argv[4])
