"""Hand fixes from listeners' reports, and (optional) journal wording."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np
from .common import journal_file, tokens, get_seconds
from .ocr_repair import FIXES

class FixNotApplied(Exception):
    """A hand fix found nothing to change: the transcript text moved under it."""


def _norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def fix_printed_times(mission, rows):
    """NASA's printed times the scan misread ("129:35:31" for 129:45:31), put
    right before anything is timed: {"g": the time as read, "text": part of
    the line, "printed": the right time in seconds}. A misread time that
    still reads as a time throws the lines after it off by minutes. Returns
    how many were put right; one that finds no line raises FixNotApplied."""
    fixes = [f for f in (json.loads(FIXES.read_text()).get(mission, []) if FIXES.exists() else []) if 'printed' in f]
    missing = []
    for f in fixes:
        hit = [r for r in rows if abs(r['getSeconds'] - f['g']) <= 2 and _norm(f['text']) in _norm(r['text'])]
        for r in hit:
            r['getSeconds'], r['getApprox'] = f['printed'], False
        if not hit and not any(r['getSeconds'] == f['printed'] and _norm(f['text']) in _norm(r['text']) for r in rows):
            missing.append(f)
    if missing:
        raise FixNotApplied('printed time fix(es) that found no line:\n' + '\n'.join(f"  GET {f['g']}: {f['text']!r}" for f in missing))
    return len(fixes)


def apply_fixes(mission, lines, strict=True, segments=None, tape_words=None):
    """Hand corrections from listeners' reports, pipeline/transcript_fixes.json:

      {"11": [{"g": GET seconds, "from": "text as printed", "to": "corrected"}, ...]}

    Each fix finds its line by time (within 2 s, else the nearest within the
    hour holding the text). "speaker" (with "text") puts a line to the right
    person; "delete": true removes a line that's a scrap of another;
    "unheard": true marks a line not on this recording; "ok": true (with
    "text") marks one a listener checked, off the review list; "review": a
    note (with "text") puts one at the top of the review list with that
    question ("Who's speaking?"); "merge": the start of the next line (with
    "text") joins that line onto this one, one sentence the scan broke in two; "split" (with
    "text", and "speaker" for the second part) cuts a line in two where the
    "split" text begins, two people run together by the scan.

    A corrected line whose time the scan lost, and any line split off, is
    timed afresh to where its words are heard (with the tapes given);
    "whole": true keys a fix on a line that is exactly its text (for short
    lines like "Roger."). "retime": true on a fix does the same for a line printed at the wrong
    time ("retime": N looks up to N seconds on, for a line printed further
    off than the usual two minutes). "at": seconds (with "text") puts a line
    at a time a listener heard it, where the recogniser can't find it.
    ("printed": a misread printed time, is fix_printed_times', before timing.)

    A fix whose "from" text is gone is still satisfied if the line already
    reads as "to" (the OCR or a rule got there first); that counts as
    applied. One that neither matches nor is already right raises
    FixNotApplied (strict), so a re-read transcript can't silently lose a
    correction. Returns how many fixes changed something."""
    fixes = json.loads(FIXES.read_text()).get(mission, []) if FIXES.exists() else []
    done, missing, fresh, moved = 0, [], {}, False   # fresh: line -> how far on to look for it
    for f in fixes:
        if 'printed' in f:
            continue   # (fix_printed_times' business, before the timing)
        key = f.get('from', f.get('text', ''))
        # "whole": the fix is for a line that is exactly this ("Roger."), not any holding it
        match = (lambda t: t.strip() == key) if f.get('delete') or f.get('whole') else (lambda t: key in t)
        hit = [l for l in lines if abs(l['g'] - f['g']) <= 2 and match(l['t'])]
        if not hit:
            near = sorted((abs(l['g'] - f['g']), k) for k, l in enumerate(lines) if abs(l['g'] - f['g']) <= 3600 and match(l['t']))
            hit = [lines[near[0][1]]] if near else []
        if hit and 'split' in f and f['split'] not in hit[0]['t'][1:]:
            hit = []
        if hit:
            for l in hit:
                if f.get('delete'):
                    l['t'] = ''
                elif f.get('unheard'):
                    l['n'] = 1
                elif 'split' in f:
                    cut = l['t'].index(f['split'], 1)
                    second = {'g': l['g'], 's': f['speaker'], 't': l['t'][cut:].strip()}
                    l['t'] = l['t'][:cut].strip()
                    lines.insert(lines.index(l) + 1, second)
                    fresh[id(second)] = 120
                elif f.get('ok'):
                    l['ok'] = 1   # a listener checked it: off the review list
                elif 'review' in f:
                    l['review'] = f['review']   # a question for a listener: top of the review list
                elif 'merge' in f:
                    rest = sorted((abs(x['g'] - l['g']), k) for k, x in enumerate(lines)
                                  if x is not l and x['t'].startswith(f['merge']) and abs(x['g'] - l['g']) <= 120)
                    if rest:
                        second = lines[rest[0][1]]
                        l['t'] = f"{l['t'].rstrip()} {second['t'].lstrip()}"
                        second['t'] = ''   # (dropped with the lines a fix deleted)
                elif 'speaker' in f:
                    l['s'] = f['speaker']
                elif 'from' in f:
                    l['t'] = l['t'].replace(f['from'], f['to'])
                    if l.get('a'):
                        fresh[id(l)] = 120
                if f.get('retime'):
                    fresh[id(l)] = 120 if f['retime'] is True else f['retime']
                if 'at' in f:
                    l['g'] = f['at']
                    l.pop('a', None)
                    fresh.pop(id(l), None)   # (the listener's time stands: no retiming it after a text fix)
                    moved = True
            done += 1
            continue
        # nothing to change: is the line already the way the fix wants it?
        if 'split' in f:
            ok = any(abs(l['g'] - f['g']) <= 3600 and l['s'] == f['speaker'] and _norm(l['t']).startswith(_norm(f['split'])) for l in lines)
        elif 'to' in f:
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['to']) in _norm(l['t']) for l in lines)
        elif 'speaker' in f:
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['text']) in _norm(l['t']) and l['s'] == f['speaker'] for l in lines)
        elif f.get('delete'):
            ok = not any(abs(l['g'] - f['g']) <= 600 and l['t'].strip() == f['text'].strip() for l in lines)
        elif 'at' in f:
            ok = any(abs(l['g'] - f['at']) <= 1 and _norm(f['text']) in _norm(l['t']) for l in lines)
        elif 'merge' in f:
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['text']) in _norm(l['t']) and _norm(f['merge']) in _norm(l['t']) for l in lines)
        elif f.get('retime'):   # (only moves a line: its text is gone, so it's been changed since)
            ok = False
        elif f.get('ok') or 'review' in f:   # (the line has changed since: the review list can judge it afresh)
            ok = True
        else:   # unheard
            ok = any(abs(l['g'] - f['g']) <= 3600 and _norm(f['text']) in _norm(l['t']) and l.get('n') for l in lines)
        if not ok:
            missing.append(f)
    if missing:
        msg = '\n'.join(f"  GET {f['g']}: {f.get('from', f.get('text'))!r}" for f in missing)
        if strict:
            raise FixNotApplied(f"{len(missing)} hand fix(es) neither matched nor already satisfied:\n{msg}")
        print(f"WARNING: {len(missing)} hand fix(es) not applied:\n{msg}")
    if fresh and segments is not None:
        from .timing import retime
        retime(lines, segments, tape_words, fresh)
        moved = True
    if moved:
        lines.sort(key=lambda l: l['g'])
    return done


def use_journal_text(mission, lines):
    """NASA's transcript is a scan read by OCR ("Cha_lie", "Ro6er"); the
    journal's transcript is the same conversation, corrected by hand. Where
    a line matches a journal line (same moment, mostly the same words), take
    the journal's wording and speaker. Returns how many lines changed."""
    journal = json.loads(journal_file('transcripts', mission).read_text())
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


