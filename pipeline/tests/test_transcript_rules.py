"""Regression checks for the transcript repair rules.

Each case is a line as NASA's scan gave it and how it must read afterwards.
They come from listeners' reports that turned into rules, so a change to a
rule that quietly breaks an earlier fix fails here instead of at the next
listening session.

    ~/.venvs/apollo/bin/python -m pytest pipeline/tests -q
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'scripts'))

from aligner import ocr_repair as R  # noqa: E402
from aligner.announcer import said_time  # noqa: E402
import nasa_transcripts as N  # noqa: E402


@pytest.fixture(scope='module')
def vocab():
    R.MISSION['n'] = '11'
    return R.vocabulary({})[0]


# (mission, text as scanned, text after the plain-slip rules)
TIDY_CASES = [
    ('11', "We'11 pass it on.", "We'll pass it on."),
    ('11', "Roger. I'11 give you another Mark.", "Roger. I'll give you another Mark."),
    ('11', 'Apollo !1, this is Houston.', 'Apollo 11, this is Houston.'),
    ('11', 'ApQiI oll, this is Houston.', 'Apollo 11, this is Houston.'),
    ('12', 'Apollo lZ, this is Houston.', 'Apollo 12, this is Houston.'),
    ('12', 'Apollo l&, Houston. Give us OMNI Charlie.', 'Apollo 12, Houston. Give us OMNI Charlie.'),
    ('11', 'You are G() at 5 minutes.', 'You are GO at 5 minutes.'),
    ('11', "You're (0 from the ground at 7 minutes.", "You're GO from the ground at 7 minutes."),
    ('11', 'That EMS DELTA-V counter is minus 4.(.', 'That EMS DELTA-V counter is minus 4.0.'),
    ('11', 'We had 0.! while ago.', 'We had 0.1 while ago.'),
    ('11', 'use bottle primary l, as per the checklist', 'use bottle primary 1, as per the checklist'),
    ('11', 'cycle pitch gimbal motor number i on', 'cycle pitch gimbal motor number 1 on'),
    ('11', 'copying you about five-ky-two, very weak', 'copying you about five-by-two, very weak'),
    ('11', 'coming in five-by-_ive here', 'coming in five-by-five here'),
    ('11', "If you'lL go ahead", "If you'll go ahead"),
    ('11', 'turn the 02 fans on manually', 'turn the O2 fans on manually'),
    ('11', 'the REPRESS 02 valve', 'the REPRESS O2 valve'),
    ('11', 'Tananarive at 37 04. Sim) lex Alfa. Houston. Out.', 'Tananarive at 37 04. Simplex Alfa. Houston. Out.'),
    ('11', 'LOS time at Canary is 23 37. / Over.', 'LOS time at Canary is 23 37. Over.'),
    ('11', "We'll be watching for Neper. Ove r.", "We'll be watching for Neper. Over."),
    ('11', 'Houston, Apollo 1t. Could you give us a time?', 'Houston, Apollo 11. Could you give us a time?'),
    ('11', 'We show PYRO bus A armed', 'We show pyro bus A armed'),
    ('11', 'the N 2 tank pressure', 'the N2 tank pressure'),
    ('11', 'Eagle, Houston. Did you call? }\'_ge 307', 'Eagle, Houston. Did you call?'),
    ('11', 'PROGRAM ALARM. iago 312', 'PROGRAM ALARM.'),
    ('11', 'What? Pase 309', 'What?'),
    ('11', 'All 12 latches arc locked. ?age 23', 'All 12 latches arc locked.'),
    ('11', 'In sports, the Houston Oilers. Page ]1t7 In Austin', 'In sports, the Houston Oilers. In Austin'),
    ('12', 'We got your E-MOD dump. i Tape 1/11', 'We got your E-MOD dump.'),
    ('12', 'everything in here. -3 NOTE', 'everything in here.'),
    ('12', 'Copy. i', 'Copy.'),
    ('12', 'for some reason. i -)', 'for some reason.'),
    ('12', 'a big piece of static electricity builder number" going through there.',
     'a big piece of static electricity builder number going through there.'),
    ('12', 'When you do your PS1, you wipe out your REFSMMAT.', 'When you do your P51, you wipe out your REFSMMAT.'),
    ('12', 'a separation time of 03 plus 18 plus 0h.', 'a separation time of 03 plus 18 plus 04.'),
    ('12', 'Ail we have is the electrical indication.', 'All we have is the electrical indication.'),
    ('12', '.. _ Houston, pyro armed.', 'Houston, pyro armed.'),
    ('11', "Roger. In'reference to 'your question", "Roger. In reference to your question"),
    ('11', 'powered descent. \',F? , }_ /\'', 'powered descent.'),
    ('11', 'Roger. i i', 'Roger.'),
    ('11', 'Roger r . We copy that', 'Roger. We copy that'),
    ('11', "We'll have them for you in a minute, Ii.", "We'll have them for you in a minute, 11."),
    ('11', 'Houston CkP COMM, Goldstone M&0 NET 1.', 'Houston CAPCOM, Goldstone M&O NET 1.'),
    ('11', 'CAP C0_, Goldstone. Roger.', 'CAPCOM, Goldstone. Roger.'),
    ('11', 'Are you receiving CAP COMM\'s voice?', "Are you receiving CAPCOM's voice?"),
    ('11', 'They started out, [ understand, and then', 'They started out, I understand, and then'),
    ('12', '] can\'t bend down that far.', "I can't bend down that far."),
    ('12', 'It is very, very ] unreal to be there.', 'It is very, very ] unreal to be there.'),   # a stray mark, not "I"
    ('12', 'Okay, we Just lost the platform, gang.', 'Okay, we just lost the platform, gang.'),
    ('12', 'Your ullage is four Jets for 11 seconds', 'Your ullage is four jets for 11 seconds'),
    ('11', 'you all are doing great Job up there.', 'you all are doing great job up there.'),
    ('11', 'We would Like you to zero', 'We would like you to zero'),
    ('11', 'officially reported to the New York Jets training camp', 'officially reported to the New York Jets training camp'),
    ('11', 'with chairman Earl Wheeler of the Joint Chiefs of Staff', 'with chairman Earl Wheeler of the Joint Chiefs of Staff'),
    ('11', 'Several other Jet players who had', 'Several other Jet players who had'),
    ('11', 'Just a second.', 'Just a second.'),   # a sentence can start with it
    ('11', '1], this is Houston. We\'ve completed the uplink.', "11, this is Houston. We've completed the uplink."),
    ('12', ']2, Houston. Go ahead.', '12, Houston. Go ahead.'),
    ('11', 'There [_age 551 are a couple of tropical storms', 'There are a couple of tropical storms'),
    ('11', 'the DIRECT O2 valve', 'the DIRECT O2 valve'),   # real O2 stays
    ('11', 'AOS Canaries at 1 50 13', 'AOS Canaries at 1 50 13'),   # numbers untouched
    ('11', "P52 is done. I'm looking at the DSKY.", "P52 is done. I'm looking at the DSKY."),   # nothing to fix
]


@pytest.mark.parametrize('mission, scanned, expected', TIDY_CASES)
def test_tidy(vocab, mission, scanned, expected):
    R.MISSION['n'] = mission
    assert R._tidy(scanned, vocab) == expected


# A misreading that can only be one word (or that the words around it settle)
UNCONFUSE_CASES = [
    ('midcou_rse', 'midcourse'),   # a stray mark inside a longer word
    ('cau_tion', 'caution'),
    ('Sta6ing', 'staging'),
    ('Cha_lie', 'charlie'),
    ('Ro6er', 'roger'),
    ('ccmplete', 'complete'),
]


@pytest.mark.parametrize('scanned, expected', UNCONFUSE_CASES)
def test_unconfuse(vocab, scanned, expected):
    spoken = {'staging', 'charlie', 'roger', 'complete', 'stating', 'midcourse', 'caution'}
    freq = {'staging': 30, 'stating': 2, 'charlie': 200, 'roger': 900, 'complete': 40}
    assert R._unconfuse(scanned, spoken | vocab, freq) == expected


# Station names and callsigns, from a mission's list
PLACE_CASES = [
    ('11', 'through Tar_n_ri_e', 'through Tananarive'),
    ('11', 'Apollo 11, this is Ho mton. Roger.', 'Apollo 11, this is Houston. Roger.'),
    ('12', "Where'd you put her down, Pete?", "Where'd you put her down, Pete?"),   # a real word never becomes a place
    ('11', 'the world awaiting your landing', 'the world awaiting your landing'),   # ("awaiting" once became "Hawaii")
]


@pytest.mark.parametrize('mission, scanned, expected', PLACE_CASES)
def test_places(vocab, mission, scanned, expected):
    R.MISSION['n'] = mission
    assert R._places(scanned, vocab) == expected


# The announcer's spoken mission time
SAID_TIME_CASES = [
    ('This is Apollo Control at 59 hours, 9 minutes.', 59 * 3600 + 9 * 60),
    ('This is Apollo Control Houston at fifty-nine hours, nine minutes into the mission.', 59 * 3600 + 9 * 60),
    ('At 78 hours, 58 minutes into the flight of Apollo 11, this is Apollo Control.', 78 * 3600 + 58 * 60),
    ('This is Apollo Control at one hundred and two hours, thirty minutes.', 102 * 3600 + 30 * 60),
    ('The crew is asleep. We will have a report shortly.', None),
]


@pytest.mark.parametrize('text, expected', SAID_TIME_CASES)
def test_said_time(text, expected):
    assert said_time(text)[0] == expected


# Merging the scan's embedded text with a Tesseract reading, word by word
def test_merge_prefers_the_reading_that_is_a_word():
    vocab = {w.lower() for w in Path('/usr/share/dict/words').read_text(errors='ignore').split()} if Path('/usr/share/dict/words').exists() else set()
    common = {'houston', 'roger', 'we', 'copy', 'that', 'the', 'and', 'about', 'the', 'change'} | vocab
    old = 'This is }{ouston. We cotied that chsnge.'
    new = 'This is Houston. We copied that change.'
    assert N.merge_readings(old, new, vocab | common, '', common) == 'This is Houston. We copied that change.'


def test_merge_keeps_a_good_word_over_a_misread():
    vocab = {'updates', 'rates', 'yates', 'yodates', 'the', 'few', 'a', 'on', 'your', 'flight', 'plan', 'items'}
    common = {'updates', 'rates', 'the', 'few', 'a', 'on', 'your', 'flight', 'plan', 'items'}
    old = 'On your flight plan items, a few updates.'
    new = 'On your flight plan items, a few yodates.'
    assert N.merge_readings(old, new, vocab, '', common) == old


def test_merge_does_not_pull_in_a_neighbours_words():
    vocab = common = {'roger', 'we', 'copy', 'stand', 'by', 'one', 'the', 'is', 'houston'}
    old = 'Roger. We copy.'
    new = 'Roger. We copy. Stand by one.'   # Tesseract ran the next line into this one
    assert N.merge_readings(old, new, vocab, 'Stand by one.', common) == 'Roger. We copy.'


# Reading NASA's time column
def test_smudged_time_takes_the_earliest_value_that_fits_between_its_neighbours():
    lo, hi = 2 * 3600 + 25 * 60 + 40, 2 * 3600 + 25 * 60 + 55
    assert N.fill_pattern('0002254?', lo, hi) == 2 * 3600 + 25 * 60 + 40
    # the neighbours narrow it: between 02:25:30 and 02:26:00, only 02:25:41 fits "00022?41"
    assert N.fill_pattern('00022?41', 2 * 3600 + 25 * 60 + 30, 2 * 3600 + 26 * 60) == 2 * 3600 + 25 * 60 + 41
    assert N.fill_pattern('00022?41', 2 * 3600 + 20 * 60, 2 * 3600 + 30 * 60) == 2 * 3600 + 20 * 60 + 41
    assert N.fill_pattern('0002?541', 2 * 3600 + 25 * 60 + 30, 2 * 3600 + 25 * 60 + 35) is None


def test_hour_only_time():
    assert N.parse_hour(['05', '09', '--', '--']) == (5 * 24 + 9) * 3600
    assert N.parse_hour(['05', '09', '12', '33']) is None


def test_speaker_codes_with_the_craft_added():
    assert N.closest_speaker('CDR-LM') == 'CDR'
    assert N.closest_speaker('SC-CM') == 'SC'
    assert N.closest_speaker('CDR-I24') == 'CDR'
    assert N.closest_speaker('CC') == 'CC'


def test_short_word_underscore_is_not_simply_dropped(vocab):
    # "ba_d" is "band" in 8-band; dropping the mark would make "bad"
    assert R._unconfuse('ba_d', {'bad', 'band', 'bald'}) != 'bad'


# Hand fixes: splitting two people run together, and timing corrected lines
# to where they're heard
def _tape(words):
    """One tape piece on the mission clock from 1000 s, with the given
    (time, word) pairs heard on it."""
    segments = [{'tape': 't', 'from': 0, 'to': 600, 'get': 1000, 'rate': 1.0}]
    ws = [(t, t + 0.3, w, w.lower()) for t, w in words]
    return segments, {'t': (ws, [w[0] for w in ws])}


def test_split_and_retime(tmp_path, monkeypatch):
    from aligner import fixes as X
    said = 'Okay. Would they call it a horizontal waviness'.split()
    said2 = "I'm not talking to them directly. Stand by Buzz".split()
    segments, tape_words = _tape([(10 + 0.4 * i, w.strip('.,?').lower()) for i, w in enumerate(said)] +
                                 [(20 + 0.4 * i, w.strip('.,?').lower().replace("'", '')) for i, w in enumerate(said2)])
    lines = [{'g': 1010, 's': 'Unknown', 't': "Okay. Would they call it a horizontal waviness? I'm not talking to them directly. Stand by, Buzz."}]
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [
        {'g': 1010, 'speaker': 'Aldrin', 'text': 'Would they call it'},
        {'g': 1010, 'text': 'Would they call it', 'split': "I'm not talking", 'speaker': 'Duke'}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    assert X.apply_fixes('11', lines, segments=segments, tape_words=tape_words) == 2
    assert [(l['s'], l['t']) for l in lines] == [('Aldrin', 'Okay. Would they call it a horizontal waviness?'),
                                                 ('Duke', "I'm not talking to them directly. Stand by, Buzz.")]
    assert abs(lines[1]['g'] - 1020) < 1   # the second part, where it's heard


def test_retime_anchors_on_the_longest_run_not_the_callsign(tmp_path, monkeypatch):
    from aligner import fixes as X
    # "Columbia, Houston" is heard first in another call; the line itself 80 s on
    segments, tape_words = _tape([(0, 'columbia'), (0.4, 'houston'), (0.8, 'logic'), (1.2, 'looks'), (1.6, 'good'),
                                  (80, 'eagle'), (80.4, 'and'), (80.8, 'columbia'), (81.2, 'houston'), (81.6, 'all'),
                                  (82, 'your'), (82.4, 'solutions'), (82.8, 'look'), (83.2, 'good')])
    lines = [{'g': 1000, 's': 'Evans', 't': 'Eagle and Columbia, Houston. All your solutions look good.', 'a': 1}]
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1000, 'from': 'look good.', 'to': 'look good to us.'}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    X.apply_fixes('11', lines, segments=segments, tape_words=tape_words)
    assert 1079 < lines[0]['g'] < 1081 and 'a' not in lines[0]


def test_a_fix_that_no_longer_matches_stops_the_run(tmp_path, monkeypatch):
    from aligner import fixes as X
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1000, 'from': 'Ro6er', 'to': 'Roger. Out.'}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    with pytest.raises(X.FixNotApplied):
        X.apply_fixes('11', [{'g': 1000, 's': 'Duke', 't': 'Copy.'}])
