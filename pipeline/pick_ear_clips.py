"""Cut short listening clips from NASA's tapes for the ear check.

For each tape it downloads a slice (by default 8 MB, about 5 minutes,
starting partway into the tape), finds the 45 seconds with the most talking
in it, and writes <tape>_<seconds into the tape>s.wav, ready for
process_audio.py. A tape given with @START (seconds) is cut there instead.

    python pipeline/pick_ear_clips.py --out $MEDIA/ear2 08/037-AAA 11/11-03301@200
    python pipeline/process_audio.py $MEDIA/ear2 --out $MEDIA/ear2 --engine deepfilternet --atten-db 12 24 --name df

Needs: curl, ffmpeg, numpy
"""
import argparse
import json
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

import numpy as np

INVENTORY = Path(__file__).parent / 'nasa_audio_inventory.json'
SR = 16000


def busiest(audio, seconds):
    """Start (in samples) of the window with the most speech: 50 ms frames
    counted as talking when 10 dB above the slice's quiet floor."""
    hop = SR // 20
    frames = audio[: len(audio) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(1)) + 1e-9)
    talking = (db > np.percentile(db, 10) + 10).astype(float)
    win = int(seconds * 20)
    if len(talking) <= win:
        return 0
    score = np.convolve(talking, np.ones(win), 'valid')
    return int(np.argmax(score)) * hop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tapes', nargs='+', help='mission/tape, e.g. 08/037-AAA, or 11/11-03301@200 for a fixed start')
    ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=float, default=45)
    ap.add_argument('--slice-mb', type=float, default=8)
    ap.add_argument('--into', type=float, default=0.4, help='where the slice starts, as a share of the tape')
    args = ap.parse_args()
    inventory = json.loads(INVENTORY.read_text())
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    for spec in args.tapes:
        mission, rest = spec.split('/')
        tape, _, fixed = rest.partition('@')
        entry = inventory[f'{int(mission):02d}']
        f = next(x for x in entry['files'] if x['format'] == 'mp3' and Path(x['name']).stem == tape)
        url = f"https://archive.org/download/{entry['item']}/{urllib.parse.quote(f['name'])}"
        with tempfile.TemporaryDirectory() as tmp:
            part = Path(tmp) / 'slice.mp3'
            if fixed:
                first = 0
                size = int((float(fixed) + args.seconds + 30) * 192000 / 8)
            else:
                first = int(f['bytes'] * args.into)
                size = int(args.slice_mb * 1e6)
            subprocess.run(['curl', '-sSfL', '--retry', '3', '-r', f'{first}-{first + size}', '-o', str(part), url], check=True)
            probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=bit_rate', '-of', 'csv=p=0', str(part)],
                                   capture_output=True, text=True).stdout.strip()
            bytes_per_s = (int(probe) if probe.isdigit() else 192000) / 8
            if fixed:
                start = float(fixed)
            else:
                raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(part), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                     capture_output=True, check=True).stdout
                start = busiest(np.frombuffer(raw, dtype=np.float32), args.seconds) / SR
            at = round(first / bytes_per_s + start)   # seconds into the whole tape
            dest = out / f'{tape}_{at}s.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start:.2f}', '-t', str(args.seconds), '-i', str(part),
                            '-ac', '1', '-ar', '48000', str(dest)], check=True)
            print(f'Apollo {int(mission)} {tape}: {at // 3600}:{at % 3600 // 60:02d}:{at % 60:02d} into the tape -> {dest.name}', flush=True)


if __name__ == '__main__':
    main()
