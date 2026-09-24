"""Work out what's on each of NASA's tapes, and where it sits in the mission.

NASA's archive doesn't say which channel a tape holds (air-to-ground, the
public-affairs broadcast with the announcer, onboard recorder, Mission
Control loops) or when it starts. For every tape this samples a few
stretches, runs speech recognition on each (forwards, and backwards to catch
tapes recorded in reverse), and:

  - flags backwards tapes (reversed audio recognises clearly, forwards doesn't);
  - scores the announcer ("This is Apollo Control, ... hours ... minutes");
  - places each stretch on the mission clock (GET) by matching its words
    against the mission transcript, and from those the tape's start GET.

    python pipeline/survey_tapes.py 11 /media/mark/T7/apollo-media/audio-orig/11 --out pipeline/tapes/apollo11.json

Needs: ffmpeg, faster-whisper (in the DeepFilterNet environment).
"""
import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
SR = 16000
SLICE = 45
WHERE = (0.12, 0.35, 0.6, 0.85)   # sample points, as a share of the tape
ANNOUNCER = re.compile(r'apollo control|this is (mission|apollo) control|ground elapsed|elapsed time|'
                       r'hours?,? \d+ minutes|flight director|public affairs', re.I)
WORD = re.compile(r"[a-z']+")


def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def audio(path, start, seconds, reverse=False):
    filt = ['-af', 'areverse'] if reverse else []
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{start:.1f}', '-t', str(seconds), '-i', str(path), *filt,
                          '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def hear(model, samples):
    segs = list(model.transcribe(samples, beam_size=1, vad_filter=False, condition_on_previous_text=False)[0])
    text = ' '.join(s.text.strip() for s in segs)
    lp = float(np.mean([s.avg_logprob for s in segs])) if segs else -9.0
    return text, lp


class Clock:
    """Finds where a snippet of speech falls in the mission transcript, by
    shared three-word sequences, weighting rare ones."""

    def __init__(self, mission):
        clips = json.loads((ROOT / 'public' / 'transcripts' / f'apollo{mission}.json').read_text())
        self.grams = defaultdict(list)   # trigram -> [get seconds]
        for lines in clips.values():
            for line in lines:
                h, m, s = (int(x) for x in line['get'].split(':'))
                t = h * 3600 + m * 60 + s
                words = WORD.findall(line['text'].lower())
                for i in range(len(words) - 2):
                    self.grams[' '.join(words[i:i + 3])].append(t)

    def place(self, text):
        """(GET seconds, score) of the best 2-minute window, or (None, 0)."""
        words = WORD.findall(text.lower())
        votes = Counter()
        # each distinct phrase counts once: recognisers sometimes loop on one line
        for gram in {' '.join(words[i:i + 3]) for i in range(len(words) - 2)}:
            hits = self.grams.get(gram, [])
            if 0 < len(hits) <= 20:   # common phrases ("roger, copy") place nothing
                for t in hits:
                    votes[t // 120] += 1 / len(hits)
        if not votes:
            return None, 0.0
        b, score = votes.most_common(1)[0]
        return b * 120 + 60, round(score, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('folder')
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', default='base.en')
    args = ap.parse_args()
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device='cpu', compute_type='int8')
    clock = Clock(f'{int(args.mission):02d}')
    out = Path(args.out)
    done = json.loads(out.read_text()) if out.exists() else {}

    tapes = sorted(Path(args.folder).glob('*.mp3'))
    for n, tape in enumerate(tapes, 1):
        if tape.stem in done:
            continue
        length = duration(tape)
        samples = []
        for w in WHERE:
            start = max(0.0, w * length - SLICE / 2)
            fwd, fwd_lp = hear(model, audio(tape, start, SLICE))
            rev, rev_lp = hear(model, audio(tape, start, SLICE, reverse=True))
            get, score = clock.place(fwd)
            samples.append({'at': round(start), 'text': fwd[:300], 'logprob': round(fwd_lp, 2), 'reversed_logprob': round(rev_lp, 2),
                            'announcer': len(ANNOUNCER.findall(fwd)), 'get': get, 'match': score,
                            'start_get': get - start if get is not None else None})
        # The tape's start: the placements that agree (within 5 min) with the best-supported one.
        placed = [s for s in samples if s['start_get'] is not None and s['match'] >= 2]
        start_get = None
        if placed:
            best = max(placed, key=lambda s: s['match'])
            agree = [s['start_get'] for s in placed if abs(s['start_get'] - best['start_get']) <= 300]
            start_get = round(float(np.median(agree))) if len(agree) >= 2 or best['match'] >= 5 else None
        backwards = sum(s['reversed_logprob'] > s['logprob'] + 0.3 for s in samples) >= 3
        done[tape.stem] = {'seconds': round(length), 'start_get': start_get, 'backwards': backwards,
                           'announcer': sum(s['announcer'] for s in samples), 'samples': samples}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(done, indent=1))
        g = f'{start_get // 3600:03d}:{start_get % 3600 // 60:02d}' if start_get is not None else '  ?   '
        print(f'[{n}/{len(tapes)}] {tape.stem}: {length / 3600:.1f} h, starts GET {g}, announcer {done[tape.stem]["announcer"]}'
              f'{", BACKWARDS" if backwards else ""}', flush=True)


if __name__ == '__main__':
    main()
