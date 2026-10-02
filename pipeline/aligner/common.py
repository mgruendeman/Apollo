"""Shared constants and helpers for the aligner: paths, crew names, tokenizing, speaker names."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent


def journal_file(kind, mission):
    """The journal's clip index ('clips') or clip transcripts ('transcripts')
    for a mission: in data/journal/ once the site plays the mission from the
    tapes (the site no longer ships them), else where the site keeps them."""
    moved = ROOT / 'data' / 'journal' / kind / f'apollo{mission}.json'
    if moved.exists():
        return moved
    return ROOT / ('src/data/clips' if kind == 'clips' else 'public/transcripts') / f'apollo{mission}.json'


MISSION = {'n': '11'}   # the mission being processed (set in main)
# Apollo 17 launched 2:40 late, and at 65 hours Mission Control set its clock ahead
# by that much to match the Flight Plan. NASA's transcript keeps time from liftoff
# (as the site does); the announcer gives the new clock's times from then on.
CLOCK_SET_AHEAD = {'17': (65 * 3600, 2 * 3600 + 40 * 60)}   # mission: (from mission time, by)


def from_liftoff(spoken):
    """A time the announcer gives, as time from liftoff."""
    at, by = CLOCK_SET_AHEAD.get(str(int(MISSION.get('n') or 0)), (None, 0))
    return spoken - by if at is not None and spoken >= at + by else spoken


TOKEN = re.compile(r"[a-z0-9]+")
CREW = {'11': {'CDR': 'Armstrong', 'CMP': 'Collins', 'LMP': 'Aldrin'},
        '12': {'CDR': 'Conrad', 'CMP': 'Gordon', 'LMP': 'Bean'},
        '14': {'CDR': 'Shepard', 'CMP': 'Roosa', 'LMP': 'Mitchell'},
        '15': {'CDR': 'Scott', 'CMP': 'Worden', 'LMP': 'Irwin'},
        '16': {'CDR': 'Young', 'CMP': 'Mattingly', 'LMP': 'Duke'},
        '17': {'CDR': 'Cernan', 'CMP': 'Evans', 'LMP': 'Schmitt'}}
OTHER = {'CT': 'Comm Tech', 'SC': 'Spacecraft', 'MS': 'Mission Control', 'HORNET': 'USS Hornet',
         'SWIM': 'Swimmer', 'MSFN': 'Tracking station', 'PAO': 'Mission Control', 'IWO': 'Recovery'}
SEARCH_S = 90          # how far from the piece's prediction to look for a line
MIN_WORDS = 3


def tokens(text):
    return TOKEN.findall(text.lower().replace("'", ''))


def get_seconds(get):
    h, m, s = (int(x) for x in get.split(':'))
    return h * 3600 + m * 60 + s


def speaker_names(mission, rows):
    """Names for NASA's codes: crew by position; for CC (the capsule
    communicator) the journal's name for whoever spoke for the ground
    nearest that time. The journal's labels are tidied: a crew member's
    onboard tag is that crew member ("Mitchell-LM": NASA's CC for Mitchell's
    "60 seconds" at the Apollo 14 landing), "LM Crew" is the spacecraft, and
    a label naming no one ("CC", "Flight controller", "Network (CapCom)")
    gives way to the nearest person the journal names."""
    journal = json.loads(journal_file('transcripts', mission).read_text())
    crew = CREW.get(mission, {})
    crew_names = set(crew.values())
    person = lambda s: (re.fullmatch(r"[A-Z][a-z]+(?:[A-Z][a-z]+)?", s) is not None and s not in crew_names
                        and s not in ('Houston', 'Recovery', 'Unknown'))

    def as_name(label):
        for c in crew_names:
            if re.match(re.escape(c) + r"[-/ (]", label):
                return c                                     # "Mitchell-LM", "Bean (on-board)"
        if re.match(r"(?i)(lm crew|unknown crew)", label):
            return 'Spacecraft'
        return label if person(label) else None

    # (the journal keeps Mission Control's clock: Apollo 17's, set ahead 2:40 at 65 hours, is brought back to time from liftoff)
    capcoms = sorted((from_liftoff(get_seconds(l['get'])), l['speaker']) for lines in journal.values() for l in lines
                     if l.get('channel', 'air-to-ground') == 'air-to-ground' and l['speaker'] not in crew_names
                     and l['speaker'] not in ('Mission Control', 'PAO'))
    people = [c for c in capcoms if person(c[1])]
    times, people_at = [t for t, _ in capcoms], [t for t, _ in people]

    def nearest(pool, at, g):
        i = min(max(bisect.bisect_left(at, g), 0), len(at) - 1)
        return min((pool[j] for j in (i - 1, i) if 0 <= j < len(pool)), key=lambda c: abs(c[0] - g))[1]

    def name(row):
        code = row['speaker']
        if code in crew:
            return crew[code]
        if code == 'CC' and capcoms:
            label = nearest(capcoms, times, row['getSeconds'])
            known = as_name(label)
            if known:
                return known
            if people:
                return nearest(people, people_at, row['getSeconds'])
            return label
        return OTHER.get(code, 'Unknown' if code == '?' else code)
    return name


