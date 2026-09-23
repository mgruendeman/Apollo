"""List NASA's Apollo audio on the Internet Archive, per mission and format.

NASA Johnson Space Center's Audio Control Room uploads its digitised Apollo
tapes to archive.org (collection "apolloaudiocollection", uploader NASA JSC).
This writes pipeline/nasa_audio_inventory.json: every audio file in each
mission's item with its format, size and length, so the download step knows
what there is and can prefer lossless files.

    python3 pipeline/survey_nasa_audio.py
"""
import json
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / 'nasa_audio_inventory.json'
ITEMS = {
    '07': 'Apollo7', '08': 'Apollo8', '09': 'Apollo9', '10': 'Apollo10', '11': 'Apollo11Audio',
    '12': 'Apollo12Audio', '13': 'Apollo13Audio', '14': 'Apollo14', '15': 'Apollo15',
    '16': 'Apollo16', '17': 'Apollo17',
}
AUDIO = {'mp3', 'flac', 'wav', 'ogg', 'm4a'}


def seconds(length):
    """archive.org lengths come as seconds ('6046.24') or 'mm:ss' / 'hh:mm:ss'."""
    if not length:
        return 0.0
    parts = [float(p) for p in str(length).split(':')]
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def main():
    inventory = {}
    for mid, item in ITEMS.items():
        meta = json.load(urllib.request.urlopen(f'https://archive.org/metadata/{item}', timeout=120))
        files = []
        for f in meta.get('files', []):
            ext = f['name'].rsplit('.', 1)[-1].lower()
            if ext in AUDIO:
                files.append({'name': f['name'], 'format': ext, 'bytes': int(f.get('size', 0) or 0),
                              'seconds': seconds(f.get('length')), 'source': f.get('source')})
        inventory[mid] = {'item': item, 'url': f'https://archive.org/details/{item}', 'files': files}
        by = {}
        for f in files:
            b = by.setdefault(f['format'], [0, 0, 0.0])
            b[0] += 1
            b[1] += f['bytes']
            b[2] += f['seconds']
        summary = ', '.join(f"{fmt}: {n} files, {gb / 1e9:.1f} GB, {sec / 3600:.0f} h" for fmt, (n, gb, sec) in sorted(by.items()))
        print(f'Apollo {mid} ({item}): {summary}', flush=True)
        time.sleep(1)
    OUT.write_text(json.dumps(inventory, indent=1) + '\n')


if __name__ == '__main__':
    main()
