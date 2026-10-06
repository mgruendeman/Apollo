"""The scanned page's own row for each line on the review list, as a small
picture: where the scan's text layer is garbage, the typed page is usually
legible to the eye (show-through from the back of the sheet fools OCR, not
a reader).

    python pipeline/page_rows.py 12 --media /media/mark/T7/apollo-media [--upload]

Reads public/review/transcript/apolloNN.json (each line's page and row),
finds the row on the page the way the scan reader does (a speaker code in
the speaker column starts a row; the lines after it without one carry it
on, and a row at the foot of a page carries on at the top of the next),
renders the row from its time stamp to the text's right edge at 170 dpi
to <media>/review-pages/NN/<page>-<row>.jpg
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

DPI = 170   # (sharp enough to pinch-zoom on a phone)


def page_rows(page, use_ocr):
    """The rows typed on a page: ([(y_top, y_bottom, text)] in PDF points,
    (x_left, x_right), head): the columns from the time stamp to the
    text's right edge, without the margin and its punch holes; head is the
    lines at the top of the page before its first row, carrying on a row
    from the page before (or None)."""
    lines = group_lines(page_words(page, use_ocr))
    spk_x = sorted(w[0] for ws in lines for w in ws if w[2].strip('.:') in SPEAKERS and w[0] > 100)
    if not spk_x:
        return [], (0, page.rect.width), None
    col = spk_x[len(spk_x) // 2]
    firsts = sorted(w[0] for ws in lines for w in ws if w[0] > col + 20)
    text_x = min(firsts) if firsts else col + 40
    rows, stamps, right, head = [], [], text_x, None   # head: a row carried over from the page before
    for ws in lines:
        if HEADER.match(' '.join(w[2] for w in ws)):
            continue
        y = ws[0][1]
        spk = [w for w in ws if abs(w[0] - col) <= 14]
        text = ' '.join(w[2] for w in ws if w[0] >= text_x - 12)
        right = max([right] + [w[0] for w in ws if w[0] >= text_x - 12])
        if spk and not spk[0][2].startswith('('):
            rows.append([y, y, text])
            digits = [w[0] for w in ws if w[0] < col - 14 and re.search(r'\d', w[2])]
            if digits:
                stamps.append(min(digits))
        elif rows and text:
            rows[-1][1] = y
            rows[-1][2] += ' ' + text
        elif not rows and text and y > 40:
            head = [y, y, text] if head is None else [head[0], y, head[2] + ' ' + text]
    x0 = (sorted(stamps)[len(stamps) // 2] - 6) if stamps else max(0, col - 70)
    x1 = min(page.rect.width - 6, right + 46)
    return rows, (max(0, x0), x1), head


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
    done, read = 0, {}
    def rows_of(pno):
        if pno not in read and 1 <= pno <= doc.page_count:
            read[pno] = page_rows(doc[pno - 1], use_ocr)
        return read.get(pno, ([], (0, 0), None))
    for pno, ls in sorted(by_page.items()):
        page = doc[pno - 1]
        rows, (x0, x1), _ = rows_of(pno)
        if not rows:
            continue
        for l in ls:
            # the row whose words are most like the line's (its place on the page can shift when the
            # reader merges or drops a row)
            key = norm(l['t'])[:60]
            best = max(range(len(rows)), key=lambda i: difflib.SequenceMatcher(None, key, norm(rows[i][2])[:60], autojunk=False).ratio())
            y0 = rows[best][0] - 9
            y1 = (rows[best + 1][0] - 3) if best + 1 < len(rows) else rows[best][1] + 12
            y1 = min(y1, rows[best][1] + 14, y0 + 300)
            clip = pymupdf.Rect(x0, y0, x1, max(y1, y0 + 16))
            pix = page.get_pixmap(dpi=DPI, clip=clip, colorspace=pymupdf.csGRAY)
            parts = [pix]
            # the last row on a page carries on at the top of the next one when the line is much
            # longer than what this page holds of it
            if best == len(rows) - 1 and len(norm(l['t'])) > 1.4 * len(norm(rows[best][2])):
                nrows, (nx0, nx1), head = rows_of(pno + 1)
                if head:
                    clip2 = pymupdf.Rect(x0, head[0] - 9, x1, min(head[1] + 14, head[0] + 300))
                    parts.append(doc[pno].get_pixmap(dpi=DPI, clip=clip2, colorspace=pymupdf.csGRAY))
            if len(parts) == 1:
                (out / f"{l['pg']}-{l['pr']}.jpg").write_bytes(pix.tobytes('jpeg', jpg_quality=72))
            else:
                from PIL import Image
                import io
                ims = [Image.open(io.BytesIO(p.tobytes('png'))) for p in parts]
                w = max(i.width for i in ims)
                sheet = Image.new('L', (w, sum(i.height for i in ims) + 6 * (len(ims) - 1)), 255)
                y = 0
                for i in ims:
                    sheet.paste(i, (0, y))
                    y += i.height + 6
                sheet.save(out / f"{l['pg']}-{l['pr']}.jpg", quality=72, optimize=True)
            done += 1
    print(f'{done} rows rendered to {out} ({len(listed)} lines listed)')
    if args.upload:
        rclone = shutil.which('rclone') or str(Path.home() / '.local/bin/rclone')
        subprocess.run([rclone, 'copy', str(out), f'r2:apollo-media/review/pages/{m}', '--transfers', '16'], check=True)
        print('uploaded')


if __name__ == '__main__':
    main()
