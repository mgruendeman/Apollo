"""Speech recognition over whole tapes, keeping every word's time on the tape.

The words are what the NASA transcript gets timed against (align_tapes.py),
so each transcript line lands on the right second of the right tape. Output
is one JSON file per tape, <out>/<tape>.json: [[start, end, word], ...].
Finished tapes are skipped, so a run can be stopped and restarted.

    python pipeline/transcribe_tapes.py /media/mark/T7/apollo-media/audio-orig/11 \\
        --tapes 155-AAA 156-AAA ... --out /media/mark/T7/apollo-media/asr/11 --jobs 4

small.en (default) is ~10x real time on 4 CPU cores and far more accurate on
these tapes than base.en. No voice-activity filter: it drops quiet speech.

Needs: faster-whisper (in the DeepFilterNet environment), ffmpeg.
"""
import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

_model = None


def _init(name, threads):
    global _model
    from faster_whisper import WhisperModel
    _model = WhisperModel(name, device='cpu', compute_type='int8', cpu_threads=threads)


def _run(src, dest):
    t = time.time()
    segs, info = _model.transcribe(str(src), beam_size=1, vad_filter=False, word_timestamps=True,
                                   condition_on_previous_text=False, language='en')
    words = [[round(w.start, 2), round(w.end, 2), w.word.strip()] for s in segs for w in (s.words or [])]
    tmp = dest.with_suffix('.part')
    tmp.write_text(json.dumps(words, separators=(',', ':')))
    tmp.rename(dest)
    return src.stem, len(words), info.duration, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--tapes', nargs='*', help='tape names (default: all .mp3 in the folder)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', default='small.en')
    ap.add_argument('--jobs', type=int, default=4, help='tapes at once; the CPU cores are shared between them')
    args = ap.parse_args()
    folder, out = Path(args.folder), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tapes = [folder / f'{t}.mp3' for t in args.tapes] if args.tapes else sorted(folder.glob('*.mp3'))
    todo = [t for t in tapes if t.exists() and not (out / f'{t.stem}.json').exists()]
    print(f'{len(todo)} tapes to do ({len(tapes) - len(todo)} done already)', flush=True)
    threads = max(1, (os.cpu_count() or 4) // max(1, args.jobs))
    start = time.time()
    with ProcessPoolExecutor(args.jobs, initializer=_init, initargs=(args.model, threads)) as pool:
        jobs = [pool.submit(_run, t, out / f'{t.stem}.json') for t in todo]
        for n, job in enumerate(as_completed(jobs), 1):
            stem, words, dur, took = job.result()
            left = (time.time() - start) / n * (len(todo) - n) / 3600
            print(f'[{n}/{len(todo)}] {stem}: {dur / 3600:.1f} h of audio, {words} words, {took / 60:.0f} min '
                  f'(about {left:.1f} h left)', flush=True)


if __name__ == '__main__':
    main()
