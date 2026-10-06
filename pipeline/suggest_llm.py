"""A model's reading of each doubtful line, for the review page's Accept button.

The page's own rule-based suggestion (aligner/review.suggest) mends a damaged
word only when a heard word has the same shape; a reviewer found it weak. This
asks Claude for the line instead, giving it everything the reviewer sees: the
line as it stands, the words heard on the tape at that moment, both readings
of the scanned row (the PDF's text layer and Tesseract's), the lines around
it, and the picture of the typed row (pipeline/page_rows.py), which the model
can read where the text layers are garbage.

    python pipeline/suggest_llm.py 12 --media /media/mark/T7/apollo-media [--limit 50] [--model sonnet] [--via api]

Two ways to ask. By default it runs through Claude Code's headless mode
(`claude -p`, the `claude` command on this machine), which uses the Claude
subscription this machine is signed in to, not a separate API bill; it
reads the row's picture itself. With --via api it uses the API instead
(ANTHROPIC_API_KEY in the environment, or ~/.config/apollo/anthropic.json
{"api_key": "..."}). Answers are cached in
<media>/suggest/NN.json by the line's time and text, so a re-run only asks
about new lines. Writes each confident answer that changes the line into
public/review/transcript/apolloNN.json as `suggest` (with `by: "model"` and
`conf`), replacing the rule-based one; align_tapes.py rewrites that file, so
run this after each alignment (or run page_rows.py first for the pictures).
"""
import argparse
import base64
import difflib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'pipeline'))

SYSTEM = """You correct one line of a NASA Apollo air-to-ground transcript. NASA typed these transcripts in 1968-72; the copy here was scanned and read by OCR, which damaged words ("Ro6er", "w±_n", "stege"), ran words together, and read page folds and margin marks as text.

You are given: the line as it stands; the words a speech recognizer heard on the tape at that moment (often noisy, sometimes the wrong stretch); two OCR readings of the same typed row (the PDF's text layer and Tesseract's); the lines before and after; and, when available, a picture of the typed row from the scanned page, which is usually legible where the text layers are not. The picture is the best evidence of what NASA typed; the tape settles what was said when the page is unreadable.

Return the text column of the line only (not the time stamp or the speaker code), as NASA typed it, with only the OCR damage mended. Where the picture shows the row running on (a second part from the top of the next page), include that continuation. Keep NASA's wording, punctuation style and capitalisation (switch names in CAPITALS, "Roger.", "Over."). Keep PAD figures as digit groups the way they were read ("plus 00185 48587 603"). Do not reword, modernise or add anything, and do not drop words that are on the page. If a word cannot be settled from the evidence, leave it as it stands rather than guess. If the whole row is scan scraps with no words on the page (a fold line, a margin note), return an empty text.

Answer with JSON only: {"text": "<the line>", "confidence": <0 to 1>, "changed": <true if your text differs from the line as it stands>}."""


def norm(t):
    return re.sub(r"[^a-z0-9]", '', t.lower())


def readings(media, m, page, text):
    """The two scan readings of this row: the row on the same page most like it in each."""
    out = {}
    for kind in ('embedded', 'tesseract'):
        path = media / 'transcripts' / f'as{m}-tec-merged.{kind}.json'
        if not path.exists():
            continue
        rows = READINGS.setdefault(str(path), json.loads(path.read_text()))
        same = [r for r in rows if r.get('page') == page]
        if not same:
            continue
        key = norm(text)[:80]
        best = max(same, key=lambda r: difflib.SequenceMatcher(None, key, norm(r['text'])[:80], autojunk=False).ratio())
        out[kind] = best['text']
    return out


READINGS = {}


def ask_claude_code(model, prompt, image_path):
    """The same question through Claude Code's headless mode, which reads the
    picture by its path (the subscription's usage, not the API's)."""
    import subprocess
    text = SYSTEM + '\n\n' + prompt
    if image_path:
        text += f'\n\nRead the picture of the typed row at {image_path} before answering.'
    cmd = ['claude', '-p', '--model', model, '--output-format', 'json', '--allowedTools', 'Read', '--max-turns', '4', text]
    for attempt in range(4):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=240, stdin=subprocess.DEVNULL)
            out = json.loads(r.stdout) if r.stdout.strip().startswith('{') else {}
            if out.get('is_error') or not out.get('result'):
                raise RuntimeError((out.get('result') or r.stderr or r.stdout)[:200])
            mt = re.search(r'\{.*\}', out['result'], re.S)
            return json.loads(mt.group(0)) if mt else None
        except Exception as e:   # (a usage limit, a hiccup: wait and try again)
            if attempt == 3:
                print(f'  failed: {e}', file=sys.stderr)
                return None
            time.sleep(20 * (attempt + 1))


def ask(client, model, prompt, image):
    content = [{'type': 'text', 'text': prompt}]
    if image:
        content.append({'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': base64.b64encode(image).decode()}})
    for attempt in range(4):
        try:
            r = client.messages.create(model=model, max_tokens=600, system=SYSTEM, messages=[{'role': 'user', 'content': content}])
            text = ''.join(b.text for b in r.content if getattr(b, 'type', '') == 'text')
            mt = re.search(r'\{.*\}', text, re.S)
            return json.loads(mt.group(0)) if mt else None
        except Exception as e:   # (a rate limit, a hiccup: wait and try again)
            if attempt == 3:
                print(f'  failed: {e}', file=sys.stderr)
                return None
            time.sleep(3 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    ap.add_argument('--via', choices=['claude-code', 'api'], default='claude-code')
    ap.add_argument('--model', default=None, help="claude-code: sonnet (default) or opus; api: claude-sonnet-5-5 (default)")
    ap.add_argument('--limit', type=int, default=0, help='only the first N listed lines (most doubtful first)')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--min-conf', type=float, default=0.5, help='keep answers at least this confident')
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    media = Path(args.media).expanduser()
    client = None
    if args.via == 'api':
        key = os.environ.get('ANTHROPIC_API_KEY')
        conf_path = Path.home() / '.config' / 'apollo' / 'anthropic.json'
        if not key and conf_path.exists():
            key = json.loads(conf_path.read_text()).get('api_key')
        if not key:
            sys.exit('No API key: set ANTHROPIC_API_KEY or put {"api_key": "..."} in ~/.config/apollo/anthropic.json')
        import anthropic
        client = anthropic.Anthropic(api_key=key)
    model = args.model or ('claude-sonnet-5-5' if args.via == 'api' else 'sonnet')
    review_path = ROOT / 'public' / 'review' / 'transcript' / f'apollo{m}.json'
    listed = json.loads(review_path.read_text())
    timeline = json.loads((ROOT / 'public' / 'timeline' / f'apollo{m}.json').read_text())
    lines = timeline['lines']
    gets = [l['g'] for l in lines]
    cache_path = media / 'suggest' / f'{m}.json'
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = [x for x in listed if f"{x['g']}|{x['t']}" not in cache][:args.limit or None]
    print(f'{len(listed)} lines listed, {len(todo)} to ask about ({args.via}, {model})')

    def context(x):
        import bisect
        k = bisect.bisect_left(gets, x['g'])
        around = [l for l in lines[max(0, k - 2):k + 3] if not (l['g'] == x['g'] and l['t'] == x['t'])][:4]
        return '\n'.join(f"  {l['s']}: {l['t'][:200]}" for l in around)

    def one(x):
        reads = readings(media, m, x.get('pg'), x['t']) if x.get('pg') else {}
        img = media / 'review-pages' / m / f"{x.get('pg')}-{x.get('pr')}.jpg" if x.get('pg') is not None else None
        image = img.read_bytes() if img and img.exists() and img.stat().st_size < 900_000 else None
        prompt = (f"Apollo {int(m)}, {x['s']} at mission time {x['g']:.0f} s.\n\n"
                  f"The line as it stands:\n{x['t']}\n\n"
                  f"Why it was flagged: {x.get('why', '')}\n\n"
                  f"Heard on the tape there:\n{x.get('tape', '(nothing heard)')}\n\n"
                  f"Scan reading, text layer:\n{reads.get('embedded', '(none)')}\n\n"
                  f"Scan reading, Tesseract:\n{reads.get('tesseract', '(none)')}\n\n"
                  f"Lines around it:\n{context(x)}\n\n"
                  + ("The picture of the typed row is attached." if image else "No picture of the row."))
        if args.via == 'api':
            return x, ask(client, model, prompt, image)
        return x, ask_claude_code(model, prompt, str(img) if image else None)

    done = 0
    with ThreadPoolExecutor(args.workers) as pool:
        for x, ans in pool.map(one, todo):
            if ans is None:
                continue
            cache[f"{x['g']}|{x['t']}"] = {'text': ans.get('text', ''), 'conf': float(ans.get('confidence', 0)), 'changed': bool(ans.get('changed'))}
            done += 1
            if done % 25 == 0:
                cache_path.write_text(json.dumps(cache, indent=0, ensure_ascii=False))
                print(f'  {done} answered', flush=True)
    cache_path.write_text(json.dumps(cache, indent=0, ensure_ascii=False))
    # into the review list: a confident answer that changes the line (or says the row is scraps)
    put = 0
    for x in listed:
        a = cache.get(f"{x['g']}|{x['t']}")
        if not a or a['conf'] < args.min_conf:
            continue
        text = a['text'].strip()
        if text and norm(text) == norm(x['t']):
            x['asTyped'] = round(a['conf'], 2)   # (the model reads the line as NASA typed it: the page ranks these last)
            continue
        x['suggest'] = text if text else ''
        x['by'] = 'model'
        x['conf'] = round(a['conf'], 2)
        put += 1
    review_path.write_text(json.dumps(listed, separators=(',', ':'), ensure_ascii=False))
    print(f'{done} answered this run; {put} suggestions on the list ({len(listed)} lines)')


if __name__ == '__main__':
    main()
