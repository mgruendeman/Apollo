"""Approve the model's confident readings without a reviewer (the reviewer's rule, 2026-10-07):
an answer of 90% or more becomes a hand fix in pipeline/transcript_fixes.json, marked
"by": "model" (so it never stops a run if a later re-read changes the line), unless the
line's speaker is unknown. A changed reading becomes a from/to fix; a line the model reads
as exactly what NASA typed becomes an "ok" (off the review list).

    python pipeline/auto_approve.py 16 --media /media/mark/T7/apollo-media [--min 0.9]

Prints how many it added. Re-align the mission afterwards (align_tapes.py), then
suggest_llm.py --apply-only, so the list shows what is left."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
norm = lambda t: re.sub(r'[^a-z0-9]', '', t.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    ap.add_argument('--min', type=float, default=0.9)
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    cache_path = Path(args.media).expanduser() / 'suggest' / f'{m}.json'
    if not cache_path.exists():
        print(f'Apollo {int(m)}: no model readings yet'); return
    cache = json.loads(cache_path.read_text())
    listed = json.loads((ROOT / 'public' / 'review' / 'transcript' / f'apollo{m}.json').read_text())
    fixes_path = ROOT / 'pipeline' / 'transcript_fixes.json'
    fixes = json.loads(fixes_path.read_text())
    have = {(f.get('g'), f.get('from', f.get('text'))) for f in fixes.get(m, [])}
    added = {'to': 0, 'ok': 0}
    for x in listed:
        a = cache.get(f"{x['g']}|{x['t']}")
        if not a or a['conf'] < args.min or x['s'] == 'Unknown':
            continue
        text = a['text'].strip()
        if not text:
            continue   # (removing a row stays the reviewer's call)
        if norm(text) == norm(x['t']):
            f = {'g': x['g'], 'text': x['t'][:80], 'ok': True, 'by': 'model'}
            kind = 'ok'
        else:
            f = {'g': x['g'], 'from': x['t'], 'to': text, 'by': 'model'}
            kind = 'to'
        key = (f['g'], f.get('from', f.get('text')))
        if key in have:
            continue
        fixes.setdefault(m, []).append(f)
        have.add(key)
        added[kind] += 1
    fixes_path.write_text(json.dumps(fixes, indent=1, ensure_ascii=False))
    print(f"Apollo {int(m)}: {added['to']} readings applied, {added['ok']} lines confirmed as typed")


if __name__ == '__main__':
    main()
