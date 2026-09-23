"""Pilot: turn a scanned NASA air-to-ground transcript PDF into structured
lines, marking the words the OCR was unsure of.

The PDFs on https://www.nasa.gov/history/mission-transcripts-mercury-gemini-and-apollo/
are page scans (as08-tec.pdf is 756 pages) with a 1999 OCR text layer that is
too garbled to use, so each page is rendered at 300 dpi and re-read with
Tesseract. Each typed row is "DD HH MM SS  SPEAKER  text", with wrapped text
on the following rows; margin marks and hole punches are dropped.

    python3 scripts/ocr_nasa_transcript.py as08-tec.pdf 100 110 > out.json

Output: [{get, speaker, text, unsure: [words], page}]
Words with Tesseract confidence below UNSURE_CONF, and words that are not in
the vocabulary of the rest of the document, go into `unsure`, which is the
list to check against the audio with speech-to-text.

Needs: pip install pymupdf; apt install tesseract-ocr
"""
import csv
import io
import json
import re
import subprocess
import sys

import pymupdf

UNSURE_CONF = 80
SPEAKERS = ['CC', 'CDR', 'CMP', 'LMP', 'SC', 'MS', 'PAO', 'IWO', 'CT', 'RECOVERY',
            'HORNET', 'SWIM', 'AIR BOSS', 'HAWAII', 'GUAYMAS', 'CARNARVON', 'BDA',
            'MSFN', 'LCC', 'CAPCOM']
# Typewriter digits that OCR commonly reads as letters
DIGIT_FIX = str.maketrans({'o': '0', 'O': '0', 'Q': '0', 'D': '0', 'l': '1', 'I': '1',
                           'i': '1', '|': '1', 'k': '4', 'h': '4', 'A': '4', 'S': '5',
                           's': '5', 'B': '8', 'g': '9', 'Z': '2', 'z': '2'})
TOKEN = r'[0-9oOQDlIi|khASsBgZz]{2}'
GET_RE = re.compile(rf'^\W*({TOKEN})\s?({TOKEN})\s?[.,]?\s?({TOKEN})\s?[.,]?\s?({TOKEN})\b\s*(.*)$')


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fix_speaker(raw):
    raw = raw.upper().strip('.,:;-— ')
    best = min(SPEAKERS, key=lambda s: edit_distance(raw, s))
    return best if edit_distance(raw, best) <= max(1, len(best) // 2) else None


def ocr_page(page):
    png = page.get_pixmap(dpi=300, colorspace=pymupdf.csGRAY).tobytes('png')
    out = subprocess.run(['tesseract', '-', '-', '--psm', '6', 'tsv'], input=png,
                         capture_output=True, check=True).stdout.decode()
    lines = {}
    for r in csv.DictReader(io.StringIO(out), delimiter='\t', quoting=csv.QUOTE_NONE):
        if r['level'] != '5' or not r['text'].strip():
            continue
        key = (int(r['block_num']), int(r['par_num']), int(r['line_num']))
        lines.setdefault(key, []).append((int(r['left']), r['text'], float(r['conf'])))
    return [sorted(ws) for _, ws in sorted(lines.items())]


def parse(pdf_path, first, last):
    doc = pymupdf.open(pdf_path)
    rows = []
    for pno in range(first, last + 1):
        page_w = doc[pno].rect.width * 300 / 72
        for words in ocr_page(doc[pno]):
            # Drop margin marks (hole punches, binder edges) left of the typed area.
            words = [w for w in words if w[0] > page_w * 0.15 and re.search(r'\w', w[1])]
            if not words:
                continue
            text = ' '.join(w[1] for w in words)
            m = GET_RE.match(text)
            if m:
                get = [g.translate(DIGIT_FIX) for g in m.group(1, 2, 3, 4)]
                rest = m.group(5).split(' ', 1)
                speaker = fix_speaker(rest[0]) if rest[0] else None
                if all(g.isdigit() for g in get) and speaker:
                    body = rest[1] if len(rest) > 1 else ''
                    n_skip = len(text.split()) - len(body.split())
                    rows.append({'get': f'{int(get[0]) * 24 + int(get[1]):03d}:{get[2]}:{get[3]}',
                                 'speaker': speaker, 'words': words[n_skip:], 'page': pno + 1})
                    continue
            # A continuation row sits in the text column; tape/page headers do not.
            if rows and not re.match(r'(?i)^\W*(tape|page|\(?goss|end of tape)', text):
                if words[0][0] > page_w * 0.35:
                    rows[-1]['words'] += words
    vocab = {}
    for r in rows:
        for _, w, c in r['words']:
            k = re.sub(r'\W', '', w.lower())
            if c >= UNSURE_CONF:
                vocab[k] = vocab.get(k, 0) + 1
    out = []
    for r in rows:
        unsure = [w for _, w, c in r['words']
                  if c < UNSURE_CONF or vocab.get(re.sub(r'\W', '', w.lower()), 0) < 2]
        out.append({'get': r['get'], 'speaker': r['speaker'],
                    'text': ' '.join(w for _, w, _ in r['words']), 'unsure': unsure, 'page': r['page']})
    return out


if __name__ == '__main__':
    json.dump(parse(sys.argv[1], int(sys.argv[2]) - 1, int(sys.argv[3]) - 1), sys.stdout, indent=1)
