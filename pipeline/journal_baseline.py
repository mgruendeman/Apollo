"""Cut the journal's version of a sample, for comparison on the ear-check page.

Given a sample made by process_audio.py (its .original.m4a) and the
apollojournals.org clip that covers the same moment, this finds where the
sample's audio sits inside the journal clip (by matching their loudness
patterns) and writes <sample>.journal.m4a: the same stretch, with only the
same loudness normalisation applied, so the page compares like with like.

    python pipeline/journal_baseline.py samples/000-AAA_60s.original.m4a \\
        https://apollojournals.org/afj/ap08fj/audio/a08_0000000.mp3 [more clip URLs...]

With several candidate clips it uses the one that matches best, and prints
how well it matched (correlation near 1 = same audio).

Needs: ffmpeg, curl, numpy
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR, HOP = 8000, 80  # envelope at 100 frames per second


def envelope(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    frames = a[: len(a) // HOP * HOP].reshape(-1, HOP)
    e = np.log1p(np.sqrt((frames ** 2).mean(1)) * 1000)
    return (e - e.mean()) / (e.std() + 1e-9)


def best_offset(sample, clip):
    """Frame offset in `clip` where `sample` fits best, and the correlation there."""
    n = len(sample)
    if len(clip) < n:
        return None, 0.0
    corr = np.correlate(clip, sample, 'valid') / n
    # normalise by the clip window's own spread
    cs, cs2 = np.cumsum(np.r_[0, clip]), np.cumsum(np.r_[0, clip ** 2])
    mean = (cs[n:] - cs[:-n]) / n
    std = np.sqrt(np.maximum((cs2[n:] - cs2[:-n]) / n - mean ** 2, 1e-9))
    corr = corr / std
    i = int(np.argmax(corr))
    return i, float(corr[i])


def main():
    sample_path, urls = Path(sys.argv[1]), sys.argv[2:]
    sample = envelope(sample_path)
    duration = len(sample) * HOP / SR
    best = None
    with tempfile.TemporaryDirectory() as tmp:
        for url in urls:
            local = Path(tmp) / url.rsplit('/', 1)[-1]
            subprocess.run(['curl', '-sSfL', '--retry', '3', '-o', str(local), url], check=True)
            off, r = best_offset(sample, envelope(local))
            print(f'{url.rsplit("/", 1)[-1]}: match {r:.2f} at {off * HOP / SR if off is not None else "-"} s')
            if off is not None and (best is None or r > best[2]):
                best = (local, off * HOP / SR, r)
        if not best:
            sys.exit('no clip long enough to match')
        local, start, r = best
        out = sample_path.with_name(sample_path.name.replace('.original.m4a', '.journal.m4a'))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start:.2f}', '-t', f'{duration:.2f}', '-i', str(local),
                        '-ac', '1', '-ar', '48000', '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11',
                        '-c:a', 'aac', '-b:a', '48k', str(out)], check=True)
        print(f'wrote {out.name} from {local.name} at {start:.1f} s (match {r:.2f})')


if __name__ == '__main__':
    main()
