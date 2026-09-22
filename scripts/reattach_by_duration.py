"""Re-attach transcript lines to clips using each clip's real audio length.

The scraper gave each clip the lines up to the next clip's start, whatever
stream that next clip belonged to. Where a journal page interleaves separate
recordings (air-to-ground, Mission Control commentary "-pao", onboard tape),
that cut clips' transcripts short and left many commentary clips empty.

Run after fetch_durations.py. For each clip with a known duration, its lines
become every line from the same journal page whose GET falls inside the
clip's audio, limited to the channels that recording contains. Clips with no
duration are dead links on the archive (404) and are dropped; their lines
stay available to any live clip whose audio covers the same moment.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLIPS = ROOT / 'src' / 'data' / 'clips'
TRANSCRIPTS = ROOT / 'public' / 'transcripts'
SNAP_SECONDS = 15 * 60


# Only missions with a real separate stream (many "-pao" / "-onboard"
# recordings, as on Apollo 8 and 13) get per-stream channel filtering;
# elsewhere one recording carries every channel.
MIN_STREAM_CLIPS = 10


def kind(clip_id):
    if re.search(r'-pao\b', clip_id, re.I):
        return 'pao'
    if re.search(r'-onboard\b', clip_id, re.I):
        return 'onboard'
    return 'a2g'


def main():
    for clips_path in sorted(CLIPS.glob('*.json')):
        clips = json.loads(clips_path.read_text())
        tr_path = TRANSCRIPTS / clips_path.name
        transcripts = json.loads(tr_path.read_text())
        has_pao = sum(kind(c['id']) == 'pao' for c in clips) >= MIN_STREAM_CLIPS
        has_onboard = sum(kind(c['id']) == 'onboard' for c in clips) >= MIN_STREAM_CLIPS

        pool = defaultdict(dict)
        for c in clips:
            for n, line in enumerate(transcripts.get(c['id'], [])):
                at = c['getSeconds'] + line['offsetSeconds']
                key = (at, line['speaker'], line['text'])
                pool[c['sourceUrl']].setdefault(key, (at, len(pool[c['sourceUrl']]), line))

        every = {'air-to-ground', 'pao', 'onboard'}
        allowed = {
            'pao': {'air-to-ground', 'pao'} if has_pao else every,
            'onboard': {'onboard'} if has_onboard else every,
            'a2g': every - ({'pao'} if has_pao else set()) - ({'onboard'} if has_onboard else set()),
        }

        live = [c for c in clips if c.get('durationSeconds')]

        # Mission Control commentary is untimed in the journals, so each
        # remark carries the GET of the radio call before it and can fall
        # just before the commentary recording that actually contains it.
        # Snap any remark not inside a commentary clip to the next one that
        # starts after it on the same page.
        snapped = defaultdict(list)
        pao_clips = defaultdict(list)
        for c in live:
            if has_pao and kind(c['id']) == 'pao':
                pao_clips[c['sourceUrl']].append(c)
        for url, page_clips in pao_clips.items():
            page_clips.sort(key=lambda c: c['getSeconds'])
            for v in pool[url].values():
                at = v[0]
                if v[2]['channel'] != 'pao':
                    continue
                if any(c['getSeconds'] <= at < c['getSeconds'] + c['durationSeconds'] for c in page_clips):
                    continue
                nxt = next((c for c in page_clips if c['getSeconds'] >= at), None)
                if nxt and nxt['getSeconds'] - at <= SNAP_SECONDS:
                    snapped[nxt['id']].append(v)
        out, before, after = {}, sum(bool(transcripts.get(c['id'])) for c in clips), 0
        for c in live:
            duration = c['durationSeconds']
            start, end = c['getSeconds'], c['getSeconds'] + duration
            channels = allowed[kind(c['id'])]
            picked = [v for v in pool[c['sourceUrl']].values()
                      if start <= v[0] < end and v[2]['channel'] in channels]
            picked += [(max(v[0], start), v[1], v[2]) for v in snapped.get(c['id'], [])]
            picked.sort(key=lambda v: (v[0], v[1]))
            if picked:
                out[c['id']] = [{**line, 'offsetSeconds': at - start} for at, _, line in picked]
                after += 1
        tr_path.write_text(json.dumps(out, indent=0, separators=(',', ':')))
        clips_path.write_text(json.dumps(live, indent=0))
        print(f'{clips_path.stem}: {len(clips) - len(live)} dead clips dropped; '
              f'clips with transcript {before}/{len(clips)} -> {after}/{len(live)}')


if __name__ == '__main__':
    main()
