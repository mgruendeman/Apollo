"""Add `durationSeconds` (read from each MP3's header) to every clip index."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp3_duration import remote_duration

CLIPS = Path(__file__).parent.parent / 'src' / 'data' / 'clips'


def one(clip):
    for _ in range(3):
        try:
            return clip['id'], remote_duration(clip['audioUrl'])
        except Exception:
            pass
    return clip['id'], None


for path in sorted(CLIPS.glob('*.json')):
    clips = json.loads(path.read_text())
    todo = [c for c in clips if not c.get('durationSeconds')]
    with ThreadPoolExecutor(12) as pool:
        got = dict(pool.map(one, todo))
    for c in clips:
        if got.get(c['id']):
            c['durationSeconds'] = round(got[c['id']], 1)
    missing = sum(1 for c in clips if not c.get('durationSeconds'))
    path.write_text(json.dumps(clips, indent=0))
    print(f'{path.name}: {len(clips)} clips, {missing} without duration', flush=True)
