"""Clean up NASA's Apollo audio for the website.

For each input file this writes two versions, the same length as the input
so transcript timing still lines up:
  <name>.original.m4a  loudness evened out only (for comparison, and for
                       listeners who want the untouched tape)
  <name>.clean.m4a     the same plus gentle speech noise reduction

Steps: decode to mono 48 kHz; cut rumble below 100 Hz; noise reduction
with DeepFilterNet (a speech-enhancement model; --atten-db caps how much
noise it may remove, which keeps voices natural) or, with --engine ffmpeg,
ffmpeg's built-in FFT denoiser; then loudness normalisation to -18 LUFS and
48 kbps mono AAC, which plays in every browser.

Tapes run for hours, so audio is processed in 60-second chunks with a short
crossfade. Finished outputs are skipped, so a run can be stopped and
restarted.

    # a whole folder of tapes
    python pipeline/process_audio.py ~/apollo-media/audio-orig/11 --out ~/apollo-media/audio/11
    # listening samples: 60 s starting 2 minutes in, two strengths
    python pipeline/process_audio.py tape.mp3 --out samples --clip 120 60 --atten-db 12 24

Needs: ffmpeg; pip install deepfilternet soundfile numpy
  (DeepFilterNet 0.5 needs torch==2.0.1 and torchaudio==2.0.2; see pipeline/README.md)
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
CHUNK_S, FADE_S = 60, 0.5
AUDIO_EXT = {'.mp3', '.flac', '.wav', '.ogg', '.m4a'}


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def decode(src, wav, clip):
    cut = ['-ss', str(clip[0]), '-t', str(clip[1])] if clip else []
    run(['ffmpeg', '-y', *cut, '-i', str(src), '-ac', '1', '-ar', str(SR), '-af', 'highpass=f=100', str(wav)])


def encode(wav, out):
    # Loudness normalisation (EBU R128), then 48 kbps mono AAC.
    run(['ffmpeg', '-y', '-i', str(wav), '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11',
         '-ar', str(SR), '-ac', '1', '-c:a', 'aac', '-b:a', '48k', '-movflags', '+faststart', str(out)])


class DeepFilter:
    def __init__(self):
        from df.enhance import init_df
        self.model, self.state, _ = init_df(log_level='ERROR')

    def __call__(self, audio, atten_db):
        import torch
        from df.enhance import enhance
        x = torch.from_numpy(audio[None, :].astype(np.float32))
        return enhance(self.model, self.state, x, atten_lim_db=atten_db).numpy()[0]


def denoise_ffmpeg(src_wav, dst_wav, atten_db):
    run(['ffmpeg', '-y', '-i', str(src_wav), '-af', f'afftdn=nr={atten_db}:nf=-30:tn=1', str(dst_wav)])


def denoise_chunks(audio, fn):
    """Apply fn to 60 s chunks with crossfaded overlaps; same length out."""
    n, step, fade = len(audio), CHUNK_S * SR, int(FADE_S * SR)
    out = np.zeros(n, dtype=np.float32)
    weight = np.zeros(n, dtype=np.float32)
    start = 0
    while start < n:
        end = min(n, start + step + fade)
        piece = fn(audio[start:end])[: end - start]
        w = np.ones(end - start, dtype=np.float32)
        if start > 0:
            w[:fade] = np.linspace(0, 1, fade)
        if end < n:
            w[-fade:] = np.linspace(1, 0, fade)
        out[start:end] += piece * w
        weight[start:end] += w
        start += step
    return out / np.maximum(weight, 1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inputs', nargs='+', help='audio files or folders')
    ap.add_argument('--out', required=True)
    ap.add_argument('--engine', choices=['deepfilternet', 'ffmpeg'], default='deepfilternet')
    ap.add_argument('--atten-db', type=float, nargs='+', default=[12],
                    help='most noise reduction allowed, in dB; give several to compare (e.g. 12 24)')
    ap.add_argument('--clip', type=float, nargs=2, metavar=('START', 'SECONDS'), help='only this part (for samples)')
    args = ap.parse_args()

    files = []
    for p in map(lambda x: Path(x).expanduser(), args.inputs):
        files += sorted(f for f in p.rglob('*') if f.suffix.lower() in AUDIO_EXT) if p.is_dir() else [p]
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    engine = DeepFilter() if args.engine == 'deepfilternet' else None

    for n, src in enumerate(files, 1):
        stem = src.stem + (f'_{int(args.clip[0])}s' if args.clip else '')
        targets = {'original': out / f'{stem}.original.m4a'}
        for db in args.atten_db:
            suffix = 'clean' if len(args.atten_db) == 1 else f'clean{int(db)}'
            targets[db] = out / f'{stem}.{suffix}.m4a'
        if all(t.exists() for t in targets.values()):
            continue
        print(f'[{n}/{len(files)}] {src.name}', flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / 'raw.wav'
            decode(src, raw, args.clip)
            if not targets['original'].exists():
                encode(raw, targets['original'])
            audio, _ = sf.read(raw, dtype='float32')
            for db in args.atten_db:
                if targets[db].exists():
                    continue
                cleaned = Path(tmp) / f'clean{db}.wav'
                if engine:
                    sf.write(cleaned, denoise_chunks(audio, lambda a: engine(a, db)), SR)
                else:
                    denoise_ffmpeg(raw, cleaned, db)
                encode(cleaned, targets[db])


if __name__ == '__main__':
    main()
