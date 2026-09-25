"""Hand fixes from listeners' reports, and (optional) journal wording."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np
from .common import ROOT, tokens, get_seconds
from .ocr_repair import FIXES

class FixNotApplied(Exception):
    """A hand fix found nothing to change: the transcript text moved under it."""


def _norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def apply_fixes(mission, lines, strict=True):
    """Hand corrections from listeners' reports, pipeline/transcript_fixes.json:

      {"11": [{"g": GET seconds, "from": "text as printed", "to": "corrected"}, ...]}

    Each fix finds its line by time (within 2 s, else the nearest within the
    hour holding the text). "speaker" (with "text") puts a line to the right
    person; "delete": true removes a line that's a scrap of another;
    "unheard": true marks a line not on this recording.

    A fix whose "from" text is gone is still satisfied if the line already
    reads as "to" (the OCR or a rule got there first); that counts as
    applied. One that neither matches nor is already right raises
    FixNotApplied (strict), so a re-read transcript can't silently lose a
    correction. Returns how many fixes changed something."""
    fixes = json.loads(FIXES.read_text()).get(mission, []) if FIXES.exists() else []
    done, missing = 0, []
    for f in fixes:
        key = f.get('from', f.get('text', ''))
        match = (lambda t: t.strip() == key) if f.get('delete') else (lambda t: key in t)
        hit = [l for l in lines if abs(l['g'] - f['g']) <= 2 and match(l['t'])]
        if not hit:
            near = sorted((abs(l['g'] - f['g']), k) for k, l in enumerate(lines) if abs(l['g'] - f['g']) <= 3600 and match(l['t']))
            hit = [lines[near[0][1]]] if near else []
        if hit:
            for l in hit:
                if f.get('delete'):
                    l['t'] = ''
                elif f.get('unheard'):
                    l['n'] = 1
                elif 'speaker' in f:
                    l['s'] = f['speaker']
                else:
                    l['t'] = l['t'].replace(f['from'], f['to'])
            done += 1
            continue
        # nothing to change: is the line already the way the fix wants it?
        if 'to' in f:
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['to']) in _norm(l['t']) for l in lines)
        elif 'speaker' in f:
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['text']) in _norm(l['t']) and l['s'] == f['speaker'] for l in lines)
        elif f.get('delete'):
            ok = not any(abs(l['g'] - f['g']) <= 600 and l['t'].strip() == f['text'].strip() for l in lines)
        else:   # unheard
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['text']) in _norm(l['t']) and l.get('n') for l in lines)
        if not ok:
            missing.append(f)
    if missing:
        msg = '\n'.join(f"  GET {f['g']}: {f.get('from', f.get('text'))!r}" for f in missing)
        if strict:
            raise FixNotApplied(f"{len(missing)} hand fix(es) neither matched nor already satisfied:\n{msg}")
        print(f"WARNING: {len(missing)} hand fix(es) not applied:\n{msg}")
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


