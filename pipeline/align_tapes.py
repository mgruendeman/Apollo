"""Time NASA's transcript to NASA's tapes, and build the mission's timeline.

Inputs, per mission:
  pipeline/tapes/apolloNN-placement.json   tape pieces placed from journal
                                           clips (place_tapes.py)
  <media>/asr/NN/<tape>.json               every recognised word with its
                                           time on the tape (transcribe_tapes.py)
  data/nasa-transcripts/asNN-tec.json      NASA's air-to-ground transcript
  public/transcripts/apolloNN.json         the journal transcript, used only
                                           to put names to NASA's speaker codes

For every NASA line in a placed piece it looks for the line's words among
the recognised words near where the piece puts it, and takes the time of
the match. Those anchors re-fit each tape's pieces exactly (the recorders
were stopped through quiet stretches, so a tape is several pieces of
mission time). Output, public/timeline/apolloNN.json:

  segments: [{tape, from, to, get, rate}]   tape seconds from..to play
                                            mission time get + rate*(t - from)
  lines:    [{g, s, t}]                     NASA's lines by mission time
                                            (seconds), speaker name, text

    python pipeline/align_tapes.py 11 --media /media/mark/T7/apollo-media
"""
import argparse
import bisect
import json
import re
from pathlib import Path

from aligner.common import ROOT, CREW, MIN_WORDS, SEARCH_S, tokens, speaker_names
from aligner.placement import find, merge_pieces, pieces_from_anchors, spoken_pieces, text_pieces, chain_anchors
from aligner.ocr_repair import MISSION, repair_ocr, vocabulary
from aligner.announcer import find_announcer
from aligner.timing import mark_unheard, rebuild_from_tape, sync_to_tape, time_untimed
from aligner.fixes import apply_fixes, use_journal_text
from aligner.review import score_lines
from aligner.segments import trim_overlaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--media', required=True)
    ap.add_argument('--journal-text', action='store_true',
                    help="take the Flight Journal's wording where a line matches (off: NASA's text, repaired from the tapes)")
    ap.add_argument('--no-strict', action='store_true',
                    help="only warn about hand fixes that no longer match (default: stop, so a re-read can't lose a correction)")
    ap.add_argument('--cleaned', action='store_true',
                    help='play our cleaned copies (uploaded to <media>/audio/NN/<tape>.clean.m4a) instead of NASA\'s originals')
    args = ap.parse_args()
    m = f'{int(args.mission):02d}'
    MISSION['n'] = m
    media = Path(args.media).expanduser()
    placement = json.loads((ROOT / 'pipeline' / 'tapes' / f'apollo{m}-placement.json').read_text())
    rows = json.loads((ROOT / 'data' / 'nasa-transcripts' / f'as{m}-tec.json').read_text())
    # NASA's introduction pages (how to read the transcript) come before the
    # first line with a printed time: not speech.
    first = next((k for k, r in enumerate(rows) if not r['getApprox']), 0)
    rows = [r for r in rows[first:] if r['getSeconds'] > 0 or r['speaker'] not in ('MS', '?')]
    name = speaker_names(m, rows)

    segments, stats, tape_words, heard_at = [], {'anchored': 0, 'tried': 0}, {}, {}
    where_heard = {}   # row index -> [(tape, tape time)] where its words were found
    grams = {}   # three-word phrases of NASA's lines (timed ones) -> their GETs
    for r in rows:
        if r['getApprox']:
            continue
        toks = tokens(r['text'])
        for k in range(len(toks) - 2):
            grams.setdefault(' '.join(toks[k:k + 3]), []).append(r['getSeconds'])
    for tape, entry in sorted(placement.items()):
        asr = media / 'asr' / m / f'{tape}.json'
        if not asr.exists():
            continue
        words = [(w[0], w[1], w[2], (tokens(w[2]) or [''])[0]) for w in json.loads(asr.read_text())]
        starts = [w[0] for w in words]
        # where to look for NASA's lines on this tape: where the journal's clips put it (if they
        # did), and where what's said on it, and the times the announcer gives, put it (a clip
        # found in the wrong place mustn't hide the rest: 177-AAA's clips put it two hours late)
        pieces = merge_pieces(list(entry.get('pieces') or []) + spoken_pieces(words) + text_pieces(words, grams))
        if not pieces:
            continue
        tape_words[tape] = (words, starts)
        anchors = []
        for piece in pieces:
            g0, g1 = piece['get_from'], piece['get_from'] + (piece['tape_to'] - piece['tape_from']) * piece['rate']
            for k, r in enumerate(rows):
                if not g0 - 60 <= r['getSeconds'] <= g1 + 60 or r['getApprox']:
                    continue
                toks = tokens(r['text'])
                if len(toks) < MIN_WORDS:
                    continue
                stats['tried'] += 1
                t_pred = piece['tape_from'] + (r['getSeconds'] - piece['get_from']) / piece['rate']
                lo = bisect.bisect_left(starts, t_pred - SEARCH_S)
                hi = bisect.bisect_right(starts, t_pred + SEARCH_S)
                t, share = find(toks, words, lo, hi)
                if t is not None and share >= 0.6:
                    anchors.append((t, r['getSeconds'], k))
                    stats['anchored'] += 1
        # (the stretches searched overlap: count each line once)
        stats['anchored'] -= len(anchors) - len(set(anchors))
        anchors = sorted(set(anchors))
        # lines between those found, where the recorder ran in bursts
        g_lo = min(p['get_from'] for p in pieces) - 60
        g_hi = max(p['get_from'] + (p['tape_to'] - p['tape_from']) * p['rate'] for p in pieces) + 60
        more = chain_anchors(rows, anchors, words, starts, g_lo, g_hi)
        stats['chained'] = stats.get('chained', 0) + len(more)
        # a line the second look places clearly keeps only that place: any other place the first
        # look found it (a stock phrase matched twice) is dropped
        again = {k for _, _, k in more}
        anchors = sorted({a for a in anchors if a[2] not in again} | set(more))
        heard_at[tape] = sorted(a[0] for a in anchors)
        for t, _, k in anchors:
            where_heard.setdefault(k, []).append((tape, t))
        for p in pieces_from_anchors(anchors, entry['seconds'], starts, [w[1] for w in words], sure=more, word_tokens=[w[3] for w in words]):
            segments.append({'tape': tape, **p})

    segments.sort(key=lambda s: s['get'])
    segments = trim_overlaps(segments)
    lines = [{'g': r['getSeconds'], 's': name(r), 't': r['text'], **({'a': 1} if r['getApprox'] else {})} for r in rows]
    synced = sync_to_tape(lines, segments, tape_words)
    untimed = time_untimed(lines, segments, tape_words)
    repaired = repair_ocr(lines, segments, tape_words)
    rebuilt = rebuild_from_tape(lines, segments, tape_words, vocabulary(tape_words)[0])
    fixed = use_journal_text(m, lines) if args.journal_text else 0
    # NASA's page headings read as if spoken ("11 AIR-TO-GROUND VOICE TRANSCRIPTION")
    lines = [l for l in lines if not re.search(r"AIR.{0,3}T.{0,4}.{0,3}G[RH]OUND|VOICE\s*T\S{0,3}[AJ]\S{0,3}S\S{0,2}R", l['t'])
             and not re.search(r"V(?:\(\)|_)[iIl]C", l['t'])   # "V()ICI,", "V_iCt,": VOICE, in a heading read worse still
             and not re.match(r"^\s*[1l]{2}\s+A\S{0,4}-", l['t'])   # "11 A_I_-TO-G][_OlJl_D VOICE ..."
             and not re.search(r"\((?:GDS|MAD|HSK|GWM|HAW|CRO|TEX|ACN|BDA|CYI|TAN|MIL|GYM)\)|there is cont.nuous|[Ss]ubsequent to TLI", l['t'])   # NASA's page note on tracking stations
             and re.search(r"[A-Za-z0-9]|\.\.\.|\*\*\*", l['t'])]   # (and lines that are only a stray mark: ")", "¢")
    out = ROOT / 'public' / 'timeline' / f'apollo{m}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    # Tapes nothing placed, though the announcer gives times on them: through
    # rest periods the recorders ran for his announcements alone, and NASA's
    # transcript has no lines to find there. Each gets a stand-in piece far off
    # the mission clock, so find_announcer moves every announcement on it to
    # the time he gives (where no other tape plays); what's left is dropped.
    OFF = -1e7
    placed = {sg['tape'] for sg in segments}
    for tape in sorted(set(tape_words) - placed):
        segments.insert(0, {'tape': tape, 'from': 0.0, 'to': float(placement[tape]['seconds']), 'get': OFF, 'rate': 1.0,
                            'standin': True})
    announcer, over, said = find_announcer(segments, lines, tape_words, heard_at)
    segments = [sg for sg in segments if not sg.get('standin') and sg['get'] > OFF / 2]
    said = [l for l in said if l['g'] > OFF / 2]
    announcer = [sp for sp in announcer if sp[0] > OFF / 2]
    over = [sp for sp in over if sp[0] > OFF / 2]
    segments = trim_overlaps(segments)
    lines = sorted(lines + said, key=lambda l: l['g'])
    for l in lines:   # station names with their capitals, the announcer's lines too
        l['t'] = re.sub(r"\b(honeysuckle|goldstone|tananarive|carnarvon|guaymas|madrid|bermuda|canberra|vanguard|redstone)\b",
                        lambda m: m.group(1).capitalize(), l['t'])
    hand = apply_fixes(m, lines, strict=not args.no_strict, segments=segments, tape_words=tape_words)
    lines = [l for l in lines if l['t']]   # (lines a hand fix deleted)
    unheard = mark_unheard(lines, segments, tape_words, media / 'envelopes' / 'tapes' / m)
    # Lines a reviewer should hear, ranked: written for the reviewer page,
    # and each line's doubt score travels with it ('q').
    vocab, _names, common, _spoken = vocabulary(tape_words)
    ranked = score_lines(lines, segments, tape_words, vocab, common)
    review = ROOT / 'public' / 'review' / 'transcript'
    review.mkdir(parents=True, exist_ok=True)
    ext = '.clean.m4a' if args.cleaned else '.mp3'
    audio = (lambda tape: f'/api/review/media/audio/{int(m)}/{tape}{ext}') if args.cleaned else \
            (lambda tape: f'https://archive.org/download/Apollo{int(m)}Audio/{tape}.mp3')
    gets_ = [sg['get'] for sg in segments]

    def where(l):   # the file and the second in it where this line plays
        k = bisect.bisect_right(gets_, l['g']) - 1
        if k < 0:
            return {}
        sg = segments[k]
        if not sg['get'] <= l['g'] <= sg['get'] + (sg['to'] - sg['from']) * sg['rate'] or sg.get('journal'):
            return {}
        return {'audio': audio(sg['tape']), 'at': round(sg['from'] + (l['g'] - sg['get']) / sg['rate'], 1)}
    (review / f'apollo{m}.json').write_text(json.dumps(
        [{'g': lines[i]['g'], 's': lines[i]['s'], 't': lines[i]['t'], 'q': q, 'why': why, **where(lines[i])} for q, i, why in ranked],
        separators=(',', ':')))
    timeline = {'mission': m, 'segments': segments, 'lines': lines, 'announcer': announcer, 'over': over}
    if args.cleaned:   # (the site fills in {media}: its media storage address)
        timeline['audio'] = {'base': f'{{media}}/audio/{int(m)}', 'ext': '.clean.m4a'}
    out.write_text(json.dumps(timeline, separators=(',', ':')))
    covered = sum((s['to'] - s['from']) * s['rate'] for s in segments) / 3600
    print(f"{stats['anchored']} of {stats['tried']} lines found on the tapes (+{stats.get('chained', 0)} between them); {len(segments)} segments covering {covered:.1f} h; "
          f"{len(lines)} lines ({repaired} words repaired from the tapes, {fixed} lines in the journal's wording, "
          f"{hand} hand fixes, {untimed} untimed lines timed from the tapes, {synced} lines timed to where they're heard, {rebuilt} rebuilt from the tapes); announcer: {len(announcer)} stretches, {sum(b - a for a, b in announcer) / 60:.0f} min, over the crew in {len(over)} places; {unheard} lines not on the recording; {len(ranked)} lines listed for review; written to {out}")


if __name__ == '__main__':
    main()

