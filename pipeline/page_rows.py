"""The scanned page's own row for each line on the review list, as a small
picture: where the scan's text layer is garbage, the typed page is usually
legible to the eye (show-through from the back of the sheet fools OCR, not
a reader).

    python pipeline/page_rows.py 12 --media /media/mark/T7/apollo-media [--upload]

Reads public/review/transcript/apolloNN.json (each line's page and row),
finds the row on the page the way the scan reader does (a speaker code in
the speaker column starts a row; the lines after it without one carry it
on), renders the row at 110 dpi to <media>/review-pages/NN/<page>-<row>.jpg
and, with --upload, copies the folder to r2:apollo-media/review/pages/NN.
The review page shows each listed line's picture from there. Rows already
rendered are kept.

Needs: pymupdf; tesseract for the early scans (Apollo 7-10).
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from nasa_transcripts import HEADER, SPEAKERS, group_lines, needs_ocr, page_words   # noqa: E402

DPI = 110


def page_rows(page, use_ocr):
    """The rows typed on a page: [(y_top, y_bottom, text)] in PDF points."""
    lines = group_lines(page_words(page, use_ocr))
    spk_x = sorted(w[0] for ws in lines for w in ws if w[2].strip('.:') in SPEAKERS and w[0] > 100)
    if not spk_x:
        return []
    col = spk_x[len(spk_x) // 2]
    firsts = sorted(w[0] for ws in lines for w in ws if w[0] > col + 20)
    text_x = min(firsts) if firsts else col + 40
    rows = []
    for ws in lines:
        if HEADER.match(' '.join(w[2] for w in ws)):
            continue
        y = ws[0][1]
        spk = [w for w in ws if abs(w[0] - col) <= 14]
        text = ' '.join(w[2] for w in ws if w[0] >= text_x - 12)
        if spk and not spk[0][2].startswith('('):
            rows.append([y, y, text])
        elif rows and text:
            rows[-1][1] = y
            rows[-1][2] += ' ' + text
    return rows


def norm(t):
    return re.sub(r"[^a-z0-9]", '', t.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    ap.add_argument('--upload', action='store_true')
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    media = Path(args.media).expanduser()
    listed = json.loads((ROOT / 'public' / 'review' / 'transcript' / f'apollo{m}.json').read_text())
    out = media / 'review-pages' / m
    out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(media / 'transcripts' / f'as{m}-tec.pdf')
    use_ocr = needs_ocr(doc)
    by_page = {}
    for l in listed:
        if 'pg' in l and not (out / f"{l['pg']}-{l['pr']}.jpg").exists():
            by_page.setdefault(l['pg'], []).append(l)
    done = 0
    for pno, ls in sorted(by_page.items()):
        page = doc[pno - 1]
        rows = page_rows(page, use_ocr)
        if not rows:
            continue
        for l in ls:
            # the row whose words are most like the line's (its place on the page can shift when the
            # reader merges or drops a row)
            key = norm(l['t'])[:60]
            best = max(range(len(rows)), key=lambda i: difflib.SequenceMatcher(None, key, norm(rows[i][2])[:60], autojunk=False).ratio())
            y0 = rows[best][0] - 9
            y1 = (rows[best + 1][0] - 3) if best + 1 < len(rows) else rows[best][1] + 12
            y1 = min(y1, rows[best][1] + 14, y0 + 90)
            clip = pymupdf.Rect(0, y0, page.rect.width, max(y1, y0 + 16))
            pix = page.get_pixmap(dpi=DPI, clip=clip, colorspace=pymupdf.csGRAY)
            (out / f"{l['pg']}-{l['pr']}.jpg").write_bytes(pix.tobytes('jpeg', jpg_quality=72))
            done += 1
    print(f'{done} rows rendered to {out} ({len(listed)} lines listed)')
    if args.upload:
        rclone = shutil.which('rclone') or str(Path.home() / '.local/bin/rclone')
        subprocess.run([rclone, 'copy', str(out), f'r2:apollo-media/review/pages/{m}', '--transfers', '16'], check=True)
        print('uploaded')


if __name__ == '__main__':
    main()
