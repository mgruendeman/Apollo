"""Download NASA's Apollo mission audio from the Internet Archive.

Reads pipeline/nasa_audio_inventory.json (from survey_nasa_audio.py) and
downloads each mission's tapes into <dest>/<mission>/, resuming partly
downloaded files and skipping finished ones, so it can be stopped and
restarted at any time.

    # everything for Apollo 11 and 12 as MP3 (about 10 + 8.5 GB)
    python3 pipeline/download_nasa_audio.py --missions 11 12 --dest /Volumes/Apollo/audio
    # lossless FLAC instead (about 10x larger)
    python3 pipeline/download_nasa_audio.py --missions 11 --format flac --dest ...
    # sample: the first 8 MB (about 5 minutes) of 2 tapes per mission
    python3 pipeline/download_nasa_audio.py --missions 8 11 13 16 --files 2 --head-mb 8 --dest ...

Needs: curl
"""
import argparse
import json
import subprocess
import urllib.parse
from pathlib import Path

INVENTORY = Path(__file__).parent / 'nasa_audio_inventory.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--missions', nargs='+', required=True, help='e.g. 8 11 13')
    ap.add_argument('--format', default='mp3', choices=['mp3', 'flac', 'ogg', 'wav'])
    ap.add_argument('--dest', required=True)
    ap.add_argument('--files', type=int, default=0, help='only the first N tapes per mission (0 = all)')
    ap.add_argument('--head-mb', type=float, default=0, help='sample mode: only the first N MB of each tape')
    args = ap.parse_args()

    inventory = json.loads(INVENTORY.read_text())
    for m in args.missions:
        mid = f'{int(m):02d}'
        entry = inventory.get(mid)
        if not entry or not entry['files']:
            print(f'Apollo {int(m)}: no audio listed (run survey_nasa_audio.py again later)')
            continue
        files = sorted((f for f in entry['files'] if f['format'] == args.format), key=lambda f: f['name'])
        if args.files:
            files = files[:args.files]
        total = sum(f['bytes'] for f in files)
        print(f"Apollo {int(m)}: {len(files)} {args.format} files, {total / 1e9:.1f} GB", flush=True)
        out_dir = Path(args.dest).expanduser() / mid
        out_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            dest = out_dir / Path(f['name']).name
            url = f"https://archive.org/download/{entry['item']}/{urllib.parse.quote(f['name'])}"
            if args.head_mb:
                if dest.exists():
                    continue
                cmd = ['curl', '-sSfL', '--retry', '5', '-r', f'0-{int(args.head_mb * 1e6)}', '-o', str(dest), url]
            else:
                if dest.exists() and dest.stat().st_size == f['bytes']:
                    continue
                # -C - resumes a partial file where it stopped
                cmd = ['curl', '-sSfL', '--retry', '5', '-C', '-', '-o', str(dest), url]
            print(f"  {f['name']} ({f['bytes'] / 1e6:.0f} MB)", flush=True)
            if subprocess.run(cmd).returncode != 0:
                print(f"  ! failed: {f['name']} (run again to retry)", flush=True)


if __name__ == '__main__':
    main()
