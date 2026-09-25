"""Shared constants and helpers for the aligner: paths, crew names, tokenizing, speaker names."""
import bisect
import difflib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
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
    communicator) the journal's name for whoever was on shift at that time."""
    journal = json.loads((ROOT / 'public' / 'transcripts' / f'apollo{mission}.json').read_text())
    crew = CREW.get(mission, {})
    crew_names = set(crew.values())
    capcoms = sorted((get_seconds(l['get']), l['speaker']) for lines in journal.values() for l in lines
                     if l.get('channel', 'air-to-ground') == 'air-to-ground' and l['speaker'] not in crew_names
                     and l['speaker'] not in ('Mission Control', 'PAO'))
    times = [t for t, _ in capcoms]

    def name(row):
        code = row['speaker']
        if code in crew:
            return crew[code]
        if code == 'CC' and capcoms:
            i = min(max(bisect.bisect_left(times, row['getSeconds']), 0), len(times) - 1)
            near = [capcoms[j] for j in (i - 1, i) if 0 <= j < len(capcoms)]
            return min(near, key=lambda c: abs(c[0] - row['getSeconds']))[1]
        return OTHER.get(code, 'Unknown' if code == '?' else code)
    return name


