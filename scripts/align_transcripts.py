"""Align each clip's transcript lines to where they are actually spoken.

The journals time each line by mission clock (GET), but a clip's audio
doesn't start exactly at its first line's GET, and pauses are sometimes cut
or kept, so GET-based offsets drift by several seconds. Mission Control
commentary is also untimed in the journals and was attached to air-to-ground
clips whose recordings don't contain it.

For each clip this runs speech recognition (faster-whisper, word
timestamps) and matches the recognised words against the transcript's words
in order. A line that matches gets the time its words are heard. Mission
Control lines that can't be found in an air-to-ground recording are dropped
from that clip; other unmatched lines (a garbled "Roger.") are placed
between their matched neighbours. Clips where too little matches (music,
heavy noise) keep their journal timing.

Recognised words are cached per clip, so re-running only re-aligns.

    python3 scripts/align_transcripts.py --cache ~/asr-cache 12 11 ...

Needs: pip install faster-whisper; curl
"""
import argparse
import json
import queue
import re
import subprocess
import tempfile
import threading
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORD_SECONDS = 0.35   # rough length of a spoken word, to back up to a line's start
MIN_FOUND = 0.3       # share of spoken lines that must match to trust a clip's alignment


def norm(word):
    return re.sub(r"[^a-z0-9]", '', word.lower().replace('rog.', 'roger'))


def spoken(text):
    # Drop the journal editors' notes: [bracketed] and (parenthetical) asides.
    return re.sub(r'\[[^\]]*\]?|\([^)]*\)', ' ', text)


def transcribe(model, path):
    # No voice-activity filter: it treats quiet, noisy radio speech as
    # silence and skips whole exchanges.
    segments, _ = model.transcribe(str(path), word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False, beam_size=1)
    return [[w.word.strip(), round(float(w.start), 2), round(float(w.end), 2)] for s in segments for w in s.words]


def forward_run(points):
    """Longest subsequence of (journal, audio, line) points increasing in both times."""
    best = []
    for i, (j, a, _) in enumerate(points):
        chain = max((best[k] for k in range(i) if points[k][0] < j and points[k][1] < a),
                    key=len, default=[])
        best.append(chain + [i])
    return [points[i] for i in max(best, key=len, default=[])]


def align(lines, words, is_pao_clip):
    """New lines list with offsetSeconds from the audio, or None to keep as is."""
    toks = [(norm(w), li, k) for li, line in enumerate(lines)
            for k, w in enumerate(spoken(line['text']).split()) if norm(w)]
    heard = [(norm(w[0]), w[1]) for w in words if norm(w[0])]
    if not toks or not heard:
        return None
    sm = SequenceMatcher(None, [t[0] for t in toks], [h[0] for h in heard], autojunk=False)
    hits = {}
    for block in sm.get_matching_blocks():
        for n in range(block.size):
            _, li, k = toks[block.a + n]
            hits.setdefault(li, []).append((k, heard[block.b + n][1]))
    line_toks = {}
    for t, li, _ in toks:
        line_toks.setdefault(li, []).append(t)

    # 1. Anchors: longer lines whose words are clearly heard, close together.
    journal = [l['offsetSeconds'] for l in lines]
    anchors = []
    for li, hs in hits.items():
        n = len(line_toks[li])
        span = hs[-1][1] - hs[0][1]
        if n >= 3 and len(hs) >= max(3, 0.5 * n) and span <= n * 0.8 + 3:
            k, t = hs[0]
            anchors.append((journal[li], max(0.0, t - k * WORD_SECONDS), li))
    anchors.sort()
    anchors = forward_run(anchors)
    anchor_at = {li: a for _, a, li in anchors}
    anchors = [(j, a) for j, a, _ in anchors]
    speakable = [li for li in line_toks]
    if not anchors or len(anchors) < max(1, MIN_FOUND * len(speakable) / 3):
        return None

    # 2. Everything else: journal spacing between the anchors either side.
    def predict(j):
        before = [p for p in anchors if p[0] <= j]
        after = [p for p in anchors if p[0] > j]
        if before and after:
            (j0, a0), (j1, a1) = before[-1], after[0]
            return a0 + (a1 - a0) * (j - j0) / (j1 - j0)
        j0, a0 = before[-1] if before else after[0]
        return a0 + (j - j0)

    times, keep = [], []
    for li, line in enumerate(lines):
        t = anchor_at.get(li)
        if t is None and li in line_toks:
            # 3. Short lines: look for their opening words near the prediction.
            guess = predict(journal[li])
            first = line_toks[li][:3]
            for i in range(len(heard) - len(first) + 1):
                if abs(heard[i][1] - guess) <= 5 and [h[0] for h in heard[i:i + len(first)]] == first:
                    t = heard[i][1]
                    break
        if t is None and line.get('channel') == 'pao' and not is_pao_clip:
            continue  # Mission Control commentary that isn't in this recording
        keep.append(line)
        times.append(t if t is not None else predict(journal[li]))
    last = 0.0
    result = []
    for line, t in zip(keep, times):
        last = max(last, t)
        result.append({**line, 'offsetSeconds': round(float(last), 1)})
    return result


def downloader(clips, cache, q):
    tmp = Path(tempfile.mkdtemp())
    for c in clips:
        if (cache / f"{c['id']}.json").exists():
            q.put((c, None))
            continue
        f = tmp / f"{c['id']}.mp3"
        ok = subprocess.run(['curl', '-sSfL', '--retry', '4', '--max-time', '900', '-o', str(f), c['audioUrl']]).returncode == 0
        q.put((c, f if ok else False))
    q.put(None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('missions', nargs='+')
    ap.add_argument('--cache', required=True)
    ap.add_argument('--model', default='tiny.en')
    args = ap.parse_args()
    cache = Path(args.cache).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device='cpu', compute_type='int8')

    for mid in args.missions:
        clips = json.loads((ROOT / 'src' / 'data' / 'clips' / f'apollo{mid}.json').read_text())
        tr_path = ROOT / 'public' / 'transcripts' / f'apollo{mid}.json'
        transcripts = json.loads(tr_path.read_text())
        todo = [c for c in clips if transcripts.get(c['id'])]
        q = queue.Queue(maxsize=3)
        threading.Thread(target=downloader, args=(todo, cache, q), daemon=True).start()
        stats = {'aligned': 0, 'kept': 0, 'failed': 0, 'dropped': 0}
        done = 0
        while (item := q.get()) is not None:
            c, f = item
            cached = cache / f"{c['id']}.json"
            if f is False:
                stats['failed'] += 1
                continue
            if f is not None:
                try:
                    cached.write_text(json.dumps(transcribe(model, f)))
                except Exception as e:  # a corrupt download shouldn't stop the run
                    print('  skip', c['id'], e, flush=True)
                    stats['failed'] += 1
                    continue
                finally:
                    f.unlink(missing_ok=True)
            words = json.loads(cached.read_text())
            lines = transcripts[c['id']]
            new = align(lines, words, bool(re.search(r'-pao\b', c['id'])))
            if new is None:
                stats['kept'] += 1
            else:
                stats['aligned'] += 1
                stats['dropped'] += len(lines) - len(new)
                transcripts[c['id']] = new
            done += 1
            if done % 25 == 0:
                tr_path.write_text(json.dumps(transcripts, indent=0, separators=(',', ':')))
                print(f'  apollo{mid}: {done}/{len(todo)} {stats}', flush=True)
        tr_path.write_text(json.dumps(transcripts, indent=0, separators=(',', ':')))
        print(f'apollo{mid} done: {stats}', flush=True)


if __name__ == '__main__':
    main()
