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
from aligner.announcer import ends_sentence, said_time, spell_names  # noqa: E402
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
    ('11', "Roger. Just a second.", "Roger. Just a second."),
    ('11', "I saw it in the flight plan, but I'm Just wondering", "I saw it in the flight plan, but I'm just wondering"),
    ('11', 'Charlie. I Just wrote it off on the fact', 'Charlie. I just wrote it off on the fact'),
    ('11', 'after the first 20 seconds, 1 would guess, of the burn', 'after the first 20 seconds, I would guess, of the burn'),
    ('12', 'No, 1 haven\'t. No, I haven\'t.', "No, I haven't. No, I haven't."),
    ('12', 'fuel cell 1 would be the one', 'fuel cell 1 would be the one'),   # a number
    ('14', "It hasn'_ gone off yet", "It hasn't gone off yet"),
    ('15', "right under the center of the IM. The IM/CSM", "right under the center of the LM. The LM/CSM"),
    ('11', "No. Don't leave thc console! It's a docked burn using th_ PTC REFSMMAT.", "No. Don't leave the console! It's a docked burn using the PTC REFSMMAT."),
    ('11', "crossing over into tile Mojave; lay a tile down", "crossing over into the Mojave; lay a tile down"),
    ('12', "we've observed th_.tthe high gain antenna", "we've observed th_.tthe high gain antenna"),   # (the tape's to mend)
    ('11', "I'd like for you tc give me the angles", "I'd like for you to give me the angles"),
    ('11', "Okay, Itm going to open up the main shutoffs.", "Okay, I'm going to open up the main shutoffs."),
    ('11', "All your systems look rea[ good to us.", "All your systems look real good to us."),
    ('14', "We re going to have to. How do you re ad?", "We're going to have to. How do you read?"),
    ('11', "Is that affirmative ? Over.", "Is that affirmative? Over."),
    ('14', "Or good evening. How are vou doing?", "Or good evening. How are you doing?"),
    ('11', "noted any erratic motions of the PC02 gage. The C02 filter", "noted any erratic motions of the PCO2 gage. The CO2 filter"),
    ('11', "It does appear to bend it slightly. The same as Apollo 10, they said.", "It does appear to bend it slightly. The same as Apollo 10, they said."),
    ('11', "a sharp vertical line on vhe picture", "a sharp vertical line on the picture"),
    ('11', "You can stay iow bit rate.", "You can stay low bit rate."),
    ('11', "would normally be picking out cur landing spot", "would normally be picking out our landing spot"),
    ('11', "Columbia's got the VHF ranging yOU. Thank yOU.", "Columbia's got the VHF ranging you. Thank you."),
    ('11', "I'm in iCS push to talk", "I'm in ICS push to talk"),
    ('11', "a front stretching fROM the center", "a front stretching from the center"),
    ('14', "Okay, sTAY for T2.", "Okay, STAY for T2."),
    ('12', "Going back to gIN cooling.", "Going back to gIN cooling."),   # (a garble: a listener's)
    ('12', "hang on to it and hand it to mc, right?", "hang on to it and hand it to me, right?"),
    ('11', "to completely depressurize th oxygen manifold", "to completely depressurize the oxygen manifold"),
    ('11', "I never hear th e last of that one", "I never hear the last of that one"),
    ('12', "we will be right wi th you.", "we will be right wi th you."),   # (a word split, not "the")
    ('12', "Okay· PLSS O2, OFF.", "Okay. PLSS O2, OFF."),
    ('11', "Do you read? Over ·", "Do you read? Over."),
    ('14', "it's your UCTA that has the · problem?", "it's your UCTA that has the problem?"),
    ('12', "· Okay, I'll scope over the ascent", "Okay, I'll scope over the ascent"),
    ('15', "We need to have you re - reinitialize the HIGH GAIN", "We need to have you re - reinitialize the HIGH GAIN"),
    ('11', "Okay. denote clipping of word and phrases.", "Okay."),
    ('11', "denote clipping of word and phrases.", ""),
    ('11', "Loud and clear. clipping of word and phrases.", "Loud and clear."),
    ('11', "Check the IMU and I'M ready", "Check the IMU and I'M ready"),
    ('12', "I oon'_ know", "I oon'_ know"),   # (not a word: the tape's business)
    ('12', 'Are you look- lng at it now?', 'Are you looking at it now?'),
    ('12', 'I was think- tng about it', 'I was thinking about it'),
    ('11', 'the voice sub- carrier part', 'the voice subcarrier part'),
    ('11', '1], this is Houston. We\'ve completed the uplink.', "11, this is Houston. We've completed the uplink."),
    ('12', ']2, Houston. Go ahead.', '12, Houston. Go ahead.'),
    ('11', 'There [_age 551 are a couple of tropical storms', 'There are a couple of tropical storms'),
    ('12', 'normal lunar COMM mode except 8-ba_d NORMAL', 'normal lunar COMM mode except S-band NORMAL'),
    ('11', 'Roger. i understand.', 'Roger. I understand.'),
    ('12', "Roger. i'll get those numbers for you.", "Roger. I'll get those numbers for you."),
    ('11', "You're good at i minute.", "You're good at 1 minute."),   # a misread 1, not I
    ('11', "we've been watching a PCO,, again.", "we've been watching a PCO, again."),
    ('11', 'minus 0265, minus 1650) 11899 36228', 'minus 0265, minus 16500 11899 36228'),
    ('11', 'Deneb and Vega, 007 144 )68. No ullage', 'Deneb and Vega, 007 144 068. No ullage'),
    ('12', 'Then CB(11) LGC/DSKY, close that.', 'Then CB(11) LGC/DSKY, close that.'),   # real parentheses
    ('12', 'Apollo 12) Houston.', 'Apollo 12) Houston.'),
    ('11', 'Roger, Nell. You are five-by.', 'Roger, Neil. You are five-by.'),
    ('11', 'We would like you to jettison Eagle a_d stationkeep', 'We would like you to jettison Eagle and stationkeep'),
    ('14', 'Check your REGs and the BATs.', 'Check your REGs and the BATs.'),   # capitals with a plural s stay
    ('11', "And that 's about the summary. We 'll see.", "And that's about the summary. We'll see."),
    ('11', 'the DIRECT O2 valve', 'the DIRECT O2 valve'),   # real O2 stays
    ('11', 'AOS Canaries at 1 50 13', 'AOS Canaries at 1 50 13'),   # numbers untouched
    ('11', 'We got you boresighted. clipping of words and phrases.', 'We got you boresighted.'),
    ('14', 'LIFT-0FF. Clock starts.', 'LIFT-OFF. Clock starts.'),   # a zero for O in a capital word
    ('12', '0key-dokey.', 'Okey-dokey.'),
    ('14', '0keydoke. Thank you.', 'Okeydoke. Thank you.'),
    ('12', 'Ckay. Go get that core tube.', 'Okay. Go get that core tube.'),
    ('11', '6o ahead.', 'Go ahead.'),
    ('11', 'when I really take my t [me and do', 'when I really take my time and do'),
    ('11', 'any buildup in humid [ty. There', 'any buildup in humidity. There'),
    ('11', 'the checklist [st dated', 'the checklist [st dated'),   # not a word joined: left
    ('14', 'about 28 hours to [sic] 27', 'about 28 hours to [sic] 27'),   # NASA's editorial note
    ('11', 'as per PGNS-20 of G&N dictionary. Over. Pat_e 43', 'as per PGNS-20 of G&N dictionary. Over.'),
    ('12', "Maybe we did it. We']] have to see.", "Maybe we did it. We'll have to see."),
    ('12', 'Okay. PF_e 465 it looks like maybe', 'Okay. it looks like maybe'),   # a page stamp mid-line
    ('12', 'from halo Pace 950 crater, or coming up', 'from halo crater, or coming up'),
    ('11', 'the 0PS pressure readings', 'the OPS pressure readings'),
    ('11', 'PROP DISPLAYS/ ENGINE 0VERRIDE/LOGIC, CLOSE.', 'PROP DISPLAYS/ ENGINE OVERRIDE/LOGIC, CLOSE.'),   # a page note's tail
    ('11', 'Traction *** seems quite good. clipping of words and phrases. 1234', 'Traction *** seems quite good.'),
    ('11', "P52 is done. I'm looking at the DSKY.", "P52 is done. I'm looking at the DSKY."),   # nothing to fix
    ('12', 'Okay. I have a good GDC, and A1 has got the fuel cells back on.', 'Okay. I have a good GDC, and Al has got the fuel cells back on.'),   # the l of Al read as a 1
    ('17', 'up around A1-Biruni and around Reiner Gamma', 'up around Al-Biruni and around Reiner Gamma'),
    ('16', 'For the Commander, A1 is still stowed, A3 is 7 hours.', 'For the Commander, A1 is still stowed, A3 is 7 hours.'),   # stowage codes stay
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


def test_announcer_names():
    assert spell_names('Jim Erwin and flight director Glenn Lunney') == 'Jim Irwin and flight director Glynn Lunney'
    assert spell_names('astronaut Carl Hennise, aboard Endeavor') == 'astronaut Karl Henize, aboard Endeavour'


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


# Placing the tapes: lines found between others, where the recorder ran in bursts
def test_in_order_keeps_the_longest_run_that_agrees_with_the_tape():
    from aligner.placement import _in_order
    # (tape time, GET, row): row 2's stock phrase was found at the wrong place on the tape
    found = [(10, 0, 0), (20, 0, 1), (5, 0, 2), (30, 0, 3), (25, 0, 4), (40, 0, 5)]
    assert [a[2] for a in _in_order(found)] == [0, 1, 4, 5]


def test_find_unique_refuses_a_readback():
    from aligner.placement import _find_unique
    pad = 'roger roll 002.5 pitch 289.3 yaw 357.5 over'.split()
    other = 'stand by we are copying the numbers now and we will get back to you in a minute on that'.split()
    back = 'roger i have roll 002.5 pitch 289.3 and yaw 357.5 over'.split()
    said = pad + other + back
    words = [(i * 0.5 + (60 if i >= len(pad) + len(other) else 0), 0, w, w) for i, w in enumerate(said)]
    # the numbers alone: said twice, 30 s apart, so no clear place
    assert _find_unique('roll 002.5 pitch 289.3 yaw 357.5'.split(), words, 0, len(words))[0] is None
    # with the words only the readback has, it's found, at its start
    t, share = _find_unique('roger i have roll 002.5 pitch 289.3 and yaw 357.5 over'.split(), words, 0, len(words))
    assert abs(t - words[len(pad) + len(other)][0]) < 0.6 and share > 0.9


def _pieces(groups, sure=()):
    """(tape time, offset) groups -> the offsets of the pieces made."""
    from aligner.placement import pieces_from_anchors
    anchors = [(t, t + off, 0) for grp in groups for t, off in grp]
    starts = sorted(t for t, _, _ in anchors)
    out = pieces_from_anchors(anchors, 10_000, starts, [t + 0.5 for t in starts], sure=[(t, t + off, 0) for t, off in sure])
    return [round(p['get'] - p['from'] * p['rate']) for p in out]


def test_a_burst_stands_as_a_piece_only_when_sure_and_well_off():
    steady = [(t, 1000) for t in (0, 10, 20, 30)]
    later = [(t, 1000) for t in (400, 410, 420, 430)]
    burst = [(200, 1100), (205, 1101)]
    assert set(_pieces([steady, burst, later])) == {1000}   # not sure: dropped (the steady stretch carries on past it)
    # sure, but its neighbours agree and it's out of line with both: a misprinted time
    assert set(_pieces([steady, burst, later], sure=burst[:1])) == {1000}
    # sure, and the tape really moves on after it (a recorder running in bursts)
    after = [(t, 1200) for t in (400, 410, 420, 430)]
    assert len(_pieces([steady, burst, after], sure=burst[:1])) == 3
    # sure but within 30 s of its neighbours: the line timing absorbs that, no new piece
    near = [(200, 1020), (205, 1021)]
    after2 = [(t, 1040) for t in (400, 410, 420, 430)]
    assert len(_pieces([steady, near, after2], sure=near[:1])) == 2


def test_ocr_twins():
    assert R._ocr_twin('Ckay', 'okay') and R._ocr_twin('Fete', 'pete') and R._ocr_twin('tnat', 'that')
    assert not R._ocr_twin('thrusted', 'trusted')   # a letter more, not a misread one
    assert not R._ocr_twin('updata', 'update')      # NASA's word for the up-data link
    assert not R._ocr_twin('rilles', 'rills')


def test_words_the_recogniser_gave_one_time_keep_their_order():
    from aligner.timing import heard_between
    segments = [{'tape': 't', 'from': 0, 'to': 100, 'get': 1000, 'rate': 1.0}]
    said = ['okay', 'thats', 'pretty', 'close', 'agreement']
    ws = [(10.0, 10.2, w, w) for w in said]   # all given the same time
    assert [h[3] for h in heard_between(segments, {'t': (ws, [w[0] for w in ws])}, 1000, 1100)] == said


def test_whole_and_retime_only_fixes(tmp_path, monkeypatch):
    from aligner import fixes as X
    segments, tape_words = _tape([(10, 'okay'), (10.4, 'ready'), (10.8, 'to'), (11.2, 'copy'),
                                  (14, 'flyby'), (14.4, 'is'), (14.8, 'the'), (15.2, 'purpose'), (15.6, 'sps'), (16, '62815')])
    lines = [{'g': 1005, 's': 'Duke', 't': 'Flyby is the purpose. SPS 62815.'},   # printed before the reply it follows
             {'g': 1010, 's': 'Aldrin', 't': 'Okay. Ready to copy.'},
             {'g': 1020, 's': 'Duke', 't': 'Roger.'}, {'g': 1021, 's': 'Aldrin', 't': 'Roger. Roger.'}]
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1005, 'text': 'Flyby is the purpose.', 'retime': True},
                                    {'g': 1021, 'from': 'Roger.', 'to': 'Rog.', 'whole': True}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    X.apply_fixes('11', lines, segments=segments, tape_words=tape_words)
    assert [l['s'] for l in lines] == ['Aldrin', 'Duke', 'Duke', 'Aldrin']   # the PAD now after "Ready to copy"
    # "whole": the line that is just "Roger." (Duke's, 1 s away), not the nearer one holding it
    assert [l['t'] for l in lines] == ['Okay. Ready to copy.', 'Flyby is the purpose. SPS 62815.', 'Rog.', 'Roger. Roger.']


def test_spaceflight_words_are_not_damage(vocab):
    for w in ('ullage', 'trunnion', 'regolith', 'pericynthion', 'stationkeeping', 'gnomon', '1/250th', '21st'):
        assert not R._suspect(w, vocab), w
    for w in ('Orl,Hi', ';J,b'):
        assert R._suspect(w, vocab), w


def test_cm_link_note_comes_out_of_the_row():
    words = lambda t: [(0, 0, w, 100.0) for w in t.split()]
    kept, note = N.strip_cm_link(words('Hello, COMMUNICATIONS Houston. How LINK do IN you USE read BETWEEN Kitty CC Hawk? AND CM'))
    assert note and ' '.join(w[2] for w in kept) == 'Hello, Houston. How do you read Kitty Hawk?'
    assert N.strip_cm_link(words('CON[_3NICATIONS LINK IN USE BETWEEN CC AND CM')) == ([], True)
    assert N.strip_cm_link(words('COMMUNICATIONS IN USE LINK BETWEEN CC AND CM')) == ([], True)
    kept, note = N.strip_cm_link(words('Roger, and we will use the link in a minute.'))
    assert not note
    assert N.strip_notes('It sounds great. OF COMMUNICATIONS BETWEEN CC AND LM RESUMED') == 'It sounds great.'
    assert N.strip_notes('Yes. You betcha. BEGIN LUNAR REV 30') == 'Yes. You betcha.'
    assert N.strip_notes('LM RESUMED 893') == ''
    assert N.strip_cm_link(words('C0_CNiCATiONS LINK IN USE BET_EN CC A}_ CM')) == ([], True)


def test_cm_link_block_runs_on_its_own_clock():
    row = lambda g, spk, text: {'getSeconds': g, 'hour': None, 'pattern': None, 'speaker': spk,
                                'words': [(0, 0, w, 100.0) for w in text.split()], 'page': 1}
    rows = [row(1000, 'CDR', 'Okay.'), row(1100, 'LMP', 'Going down.'), row(1200, 'CDR', 'Down.'),
            row(None, '?', 'COMMUNICATIONS LINK IN USE BETWEEN CC AND CM'),
            row(900, 'CMP', 'Hello, Houston.'), row(None, 'CC', 'Go ahead.'), row(1150, 'CMP', 'Roger.'),
            row(1210, 'LMP', 'Okay, Dave.'), row(1220, 'CDR', 'Here we go.')]
    streams = N.cm_link_streams(rows)
    assert streams == [0, 0, 0, 1, 1, 1, 1, 0, 0]
    N.resolve_times(rows, streams)
    assert [r['getSeconds'] for r in rows] == [1000, 1100, 1200, 900, 900, 900, 1150, 1210, 1220]
    assert not any(r['getApprox'] for i, r in enumerate(rows) if i not in (3, 5))


def test_a_delayed_playback_starts_at_its_first_line_and_the_live_talk_runs_to_the_announcer():
    from aligner.placement import pieces_from_anchors
    # live talk at offset 1000 up to 60 s; the announcer takes over at 70 s ("This is Apollo Control ...");
    # from 100 s a playback of earlier talk, at offset 910 (90 s back in mission time)
    said = [(t, w) for t, w in [(10, 'roger'), (20, 'copy'), (30, 'go'), (40, 'ahead'), (55, 'likewise'),
                                (70, 'this'), (70.4, 'is'), (70.8, 'apollo'), (71.2, 'control'), (72, 'at'), (80, 'news'),
                                (100, 'roger'), (110, 'eleven'), (120, 'angles'), (130, 'roll')]]
    starts = [t for t, _ in said]
    anchors = [(10, 1010, 0), (20, 1020, 1), (40, 1040, 2), (100, 1010, 3), (110, 1020, 4), (120, 1030, 5)]
    pieces = pieces_from_anchors(anchors, 200, starts, [t + 0.3 for t in starts], sure=anchors[3:],
                                 word_tokens=[w for _, w in said])
    live, playback = pieces
    assert 69 < live['to'] <= 70.8          # the live piece keeps the talk, up to the announcer
    assert 80 < playback['from'] <= 100     # the playback starts just before its first line
    assert abs(playback['get'] - (playback['from'] + 910)) < 1


def test_a_title_does_not_end_the_announcers_sentence():
    assert ends_sentence('birthday.') and ends_sentence('now?')
    assert not ends_sentence('Dr.') and not ends_sentence('Mrs.') and not ends_sentence('Paine')
    assert not ends_sentence('O.')   # Thomas O. Paine


def test_a_line_marked_fine_leaves_the_review_list(tmp_path, monkeypatch):
    from aligner import fixes as X
    from aligner.review import score_lines
    lines = [{'g': 1000, 's': 'Unknown', 't': 'All that soot, huh?', 'a': 1}]   # time lost, speaker unknown: listed
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1000, 'text': 'All that soot, huh?', 'ok': True}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    assert X.apply_fixes('11', lines) == 1
    assert lines[0].get('ok') and lines[0]['t'] == 'All that soot, huh?'
    assert score_lines(lines, [], {}, set()) == []
    del lines[0]['ok']
    assert len(score_lines(lines, [], {}, set())) == 1


def test_a_press_conference_on_the_tape_marks_the_lines_under_it_not_on_this_recording():
    from aligner.timing import mark_drowned_out
    # the tape plays a press conference from 0 to 600 s; NASA's lines there aren't on it; then the crew are heard
    press = [(t, t + 0.3, w, w) for t, w in zip(range(0, 600, 2), __import__('itertools').cycle(['question', 'about', 'the', 'rover', 'budget', 'answer']))]
    crew = [(600 + 0.4 * i, 600 + 0.4 * i + 0.3, w, w) for i, w in enumerate('houston intrepid we read you loud and clear'.split())]
    ws = press + crew
    segments = [{'tape': 't', 'from': 0, 'to': 700, 'get': 1000, 'rate': 1.0}]
    tape_words = {'t': (ws, [w[0] for w in ws])}
    said = ['Intrepid, one additional word on the checklist cards.', 'Understand the checklist cards.', 'Pete, Jane sends her congratulations tonight.',
            'Thank you, Houston.', 'We will be coming upon the PLSS check shortly.', 'Standing by for your readings.', 'Confirm you kept the bracket there.']
    lines = [{'g': 1020 + 80 * i, 's': 'Gibson', 't': t} for i, t in enumerate(said)] + [{'g': 1601, 's': 'Bean', 't': 'Houston, Intrepid. We read you loud and clear.'}]
    assert mark_drowned_out(lines, segments, tape_words) == 7
    assert [bool(l.get('n')) for l in lines] == [True] * 7 + [False]


def test_a_line_put_where_a_listener_heard_it(tmp_path, monkeypatch):
    from aligner import fixes as X
    lines = [{'g': 1000, 's': 'Collins', 't': 'Will do.'}, {'g': 1010, 's': 'Duke', 't': 'Can you stationkeep with it, Mike?'}]
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1000, 'text': 'Will do.', 'at': 1015}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    assert X.apply_fixes('11', lines) == 1
    assert [(l['g'], l['t']) for l in lines] == [(1010, 'Can you stationkeep with it, Mike?'), (1015, 'Will do.')]


def test_a_question_for_a_listener_tops_the_review_list(tmp_path, monkeypatch):
    from aligner import fixes as X
    from aligner.review import score_lines
    lines = [{'g': 1000, 's': 'Unknown', 't': 'Okay, Pete. Let me level it up.'}, {'g': 1010, 's': 'Duke', 't': 'Rog3r, Houst0n.', 'a': 1}]
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'12': [{'g': 1000, 'text': 'Okay, Pete. Let me level it up.', 'review': "Who's speaking?"}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    assert X.apply_fixes('12', lines) == 1
    ranked = score_lines(lines, [], {}, set())
    assert ranked[0][1] == 0 and ranked[0][0] == 100 and ranked[0][2].startswith("Who's speaking?")


def test_an_acronym_the_recogniser_spells_differently_is_not_a_misread():
    from aligner.review import _disagreements
    assert _disagreements('About 2 minutes to LOS on this pass'.split(), 'about 2 minutes to lls on this pass'.split()) == []
    assert _disagreements('Evasive maneuver SPS G&N: 63481'.split(), 'evasive maneuver sps gnn 63481'.split()) == []
    assert _disagreements('We read ycu loud'.split(), 'we read you loud'.split()) == [('ycu', 'you')]


def test_a_pinned_stretch_of_tape_replaces_what_covered_it():
    from aligner.segments import pin_pieces
    pieces = [{'from': 0, 'to': 100, 'get': 1000, 'rate': 1.0, 'anchors': 3}, {'from': 100, 'to': 300, 'get': 500, 'rate': 1.0, 'anchors': 1},
              {'from': 300, 'to': 600, 'get': 2300, 'rate': 1.0, 'anchors': 4}]
    out = pin_pieces(pieces, [{'tape_from': 80, 'tape_to': 320, 'get_from': 2080}])
    assert [(p['from'], p['to'], p['get']) for p in out] == [(0, 80, 1000), (80, 320, 2080), (320, 600, 2320)]


def test_photos_between_two_anchors_spread_evenly_by_frame_number():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from photo_times import times_for
    frames = ['AS11-40-5844', 'AS11-40-5845', 'AS11-40-5854', 'AS11-40-5864', 'AS11-40-5870']
    t = times_for(frames, [(5844, 1000), (5864, 2000)])
    assert t == {'AS11-40-5844': 1000, 'AS11-40-5845': 1050, 'AS11-40-5854': 1500, 'AS11-40-5864': 2000, 'AS11-40-5870': 2000}


def test_a_sentence_the_scan_broke_in_two_joins_up(tmp_path, monkeypatch):
    from aligner import fixes as X
    lines = [{'g': 1000, 's': 'Armstrong', 't': 'You want him to go to high gain yaw 0? Say'}, {'g': 1000, 's': 'Unknown', 't': 'again the numbers.', 'a': 1},
             {'g': 1010, 's': 'Duke', 't': 'Roger, Neil.'}]
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1000, 'text': 'You want him to go to high gain', 'merge': 'again the numbers.'}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    assert X.apply_fixes('11', lines) == 1
    assert [l['t'] for l in lines if l['t']] == ['You want him to go to high gain yaw 0? Say again the numbers.', 'Roger, Neil.']


def _spoken(*parts):
    """Recognised words [[start, end, word]] from (start second, text) parts, a word every 0.4 s."""
    out = []
    for t, text in parts:
        for k, word in enumerate(text.split()):
            out.append([t + 0.4 * k, t + 0.4 * k + 0.3, word])
    return out


def test_announcer_runs_on_past_a_pause_and_back_from_a_sign_off_but_not_into_the_crew():
    from aligner.announcer import find_announcer
    words = _spoken((10, 'Roger, Houston. Reading you loud and clear.'),
                    (20, 'This is Apollo Control. All is well aboard the spacecraft.'),
                    (30, 'The crew is now eating a meal before the rest period.'),     # after a 5 s pause: still him
                    (42, 'Nice, over. Roger, Houston. Read you the same.'),             # after a 7 s pause: the crew
                    (94, 'The spacecraft is now well on its way to the Moon.'),
                    (99.5, 'The crew is at rest and all systems are normal at this time.'),
                    (106, 'And this is Apollo Control.'))                               # a sign-off: back to his start
    segments = [{'tape': 'T', 'from': 0, 'to': 200, 'get': 1000, 'rate': 1.0}]
    lines = [{'g': 1010, 's': 'Aldrin', 't': 'Roger, Houston. Reading you loud and clear.'}]
    spans, over, said = find_announcer(segments, lines, {'T': (words,)}, {'T': [10]})
    assert [[round(a), round(b)] for a, b in spans] == [[1020, 1035], [1094, 1108]]
    assert not any('Nice' in l['t'] for l in said)
    assert said[-3]['t'] == 'The spacecraft is now well on its way to the Moon.'


def test_apollo_17_announcer_times_after_the_clock_was_set_ahead():
    from aligner.announcer import from_liftoff
    from aligner.ocr_repair import MISSION
    MISSION['n'] = '17'
    assert from_liftoff(60 * 3600) == 60 * 3600                  # before 65 hours: as said
    assert from_liftoff(115 * 3600) == 115 * 3600 - 9600         # "Apollo Control at 115 hours": 112:20 from liftoff
    MISSION['n'] = '16'
    assert from_liftoff(115 * 3600) == 115 * 3600                       # Apollo 16: before its first update
    assert from_liftoff(139 * 3600 + 25 * 60) == 139 * 3600 + 13 * 60 + 12   # 11:48 ahead from 118:06
    assert from_liftoff(240 * 3600 + 38 * 60) == 215 * 3600 + 52 * 60   # and 24:46 ahead from 202:18
    MISSION['n'] = '14'
    assert from_liftoff(50 * 3600) == 50 * 3600
    assert from_liftoff(142 * 3600) == pytest.approx(141 * 3600 + 19 * 60 + 57.1)   # 40:02.9 ahead from 54:53
    MISSION['n'] = '11'
    assert from_liftoff(150 * 3600) == 150 * 3600


def test_page_headings_the_scan_ran_into_a_line_are_taken_out():
    from aligner.ocr_repair import _page_heading
    assert _page_heading("And we owe him an 06 20, whenever he gets stopped. Tap'e69/5") == "And we owe him an 06 20, whenever he gets stopped."
    assert _page_heading("we'll send up your target load I Tape 52/6 and your REFSMMAT") == "we'll send up your target load and your REFSMMAT"
    assert _page_heading("Here's a beauty. I Tape 86/_5") == "Here's a beauty."
    assert _page_heading("Okay; understand. Tape 77/]") == "Okay; understand."
    assert _page_heading("Okay. Page 762") == "Okay."
    assert _page_heading("Open hatch slowly, and verify that our hex clears. rape 170/35") == "Open hatch slowly, and verify that our hex clears."
    assert _page_heading("Say, Houston, 12. i Tape h/2 [ D") == "Say, Houston, 12."
    assert _page_heading("How much fuel did I I Tape 3/4 i Page 26") == "How much fuel did I"
    assert _page_heading("You're looking at, Houston. I Tape 1_1/15 '1") == "You're looking at, Houston."
    assert _page_heading("I'm approaching the Emplemus side. Page 598") == "I'm approaching the Emplemus side."
    assert _page_heading("I taped 2/3 of it. Turn to page 12 now.") == "I taped 2/3 of it. Turn to page 12 now."


# Apollo 17: each tape transcribed as two (A the lunar module's link, B the
# command module's), and a time printed only where an exchange starts
def test_tape_letters_make_the_command_modules_pages_their_own_blocks():
    row = lambda page, g, spk: {'getSeconds': g, 'hour': None, 'pattern': None, 'speaker': spk, 'words': [(0, 0, 'Okay.', 100.0)], 'page': page}
    letters = {p: 'A' for p in range(10, 40)}
    letters.update({p: 'B' for p in range(20, 30)})
    letters[5] = 'B'      # a lone "2B/3" far from the lettered pages: 28/3 misread
    letters[24] = None    # a heading the scan couldn't read, on a page where the CMP speaks
    letters[33] = None    # and one where nobody settles it: with the page before
    rows = [row(5, 100, 'CMP'), row(12, 1000, 'CDR'), row(19, 2000, 'LMP'),
            row(20, 1500, 'CMP'), row(24, 1700, 'CMP'), row(29, 9000000, 'CMP'), row(29, 2500, 'CC'),
            row(30, 2100, 'CDR'), row(33, None, 'CC'), row(39, 2600, 'LMP')]
    streams = N.tape_letter_streams(rows, letters)
    assert streams == [0, 0, 0, 1, 1, 1, 1, 0, 0, 0]
    N.resolve_times(rows, streams)
    # the lunar module's times run on past the block; the block keeps its own; a time far off (a misread day) isn't trusted
    assert [r['getSeconds'] for r in rows] == [100, 1000, 2000, 1500, 1700, 1700, 2500, 2100, 2100, 2600]
    assert [r['getApprox'] for r in rows] == [False, False, False, False, False, True, False, False, True, False]
    assert N.tape_letter_streams(rows, {p: None for p in range(40)}) == [0] * len(rows)   # no lettered tapes: one stream


def test_tape_letter_from_a_page_heading():
    line = lambda text: [[(0, 0, w, 100.0) for w in text.split()]]
    assert N.tape_letter(line('Tape 80B/1')) == 'B'
    assert N.tape_letter(line('Tape 8lA/14')) == 'A'
    assert N.tape_letter(line('Tape 28/3')) is None
    assert N.tape_letter(line('Tape B/5')) is None      # "3/5" misread
    assert N.tape_letter(line('APOLLO 17 AIR-TO-GROUND VOICE TRANSCRIPTION')) is None


def test_a_long_run_of_untimed_lines_is_lined_up_with_the_tape_at_once():
    from aligner.timing import time_untimed
    said = ("houston we are at station two . okay copy that . there is a big boulder here with white clasts . "
            "okay that is good . i will get a sample of the white clast . bag four seven six . copy four seven six . "
            "now the gray matrix . okay that is good . that one is in bag four seven seven . and the soil beside it . "
            "okay we see you on the television . we are moving on to the rake sample now").replace(' .', '').split()
    segments, tape = _tape([(10 + 0.5 * k, w) for k, w in enumerate(said)])
    text = ["Houston, we are at station 2.", "Okay, copy that.", "There is a big boulder here with white clasts.", "Okay, that is good.",
            "I will get a sample of the white clast.", "Bag four seven six.", "Copy four seven six.", "Now the gray matrix.",
            "Okay, that is good.", "That one is in bag four seven seven.", "And the soil beside it.", "Okay, we see you on the television.",
            "We are moving on to the rake sample now."]
    lines = [{'g': 1010, 's': 'Schmitt', 't': text[0]}] + [{'g': 1010, 's': 'x', 't': t, 'a': 1} for t in text[1:-1]] \
        + [{'g': 1010 + 0.5 * said.index('moving') - 1, 's': 'Cernan', 't': text[-1]}]
    cm = {'g': 1015, 's': 'Evans', 't': 'Houston, America. The mapping camera is off.'}   # the other loop's line, timed, in among them
    lines.insert(4, cm)
    assert time_untimed(lines, segments, tape, other_loop={id(cm)}) == 11
    where = lambda t, nth=0: 1010 + 0.5 * [k for k in range(len(said)) if said[k:k + 2] == t.split()][nth]
    got = {l['t']: l['g'] for l in lines if l is not cm}
    assert abs([l['g'] for l in lines if l['t'] == 'Okay, that is good.'][1] - where('okay that', 1)) <= 1   # the second "that is good", not the first
    assert abs(got['Now the gray matrix.'] - where('now the')) <= 1
    assert abs(got['Okay, we see you on the television.'] - where('okay we')) <= 1
    assert not any(l.get('a') for l in lines)


def test_a_long_line_is_found_before_a_time_printed_late():
    from aligner.timing import sync_to_tape
    said = "okay houston there is the classic raindrop pattern over this fine debris".split()
    segments, tape = _tape([(100 + 0.4 * k, w) for k, w in enumerate(said)] + [(200, 'copy'), (200.4, 'that'), (200.8, 'jack')])
    lines = [{'g': 1158, 's': 'Schmitt', 't': "Okay, Houston. There's - the classic raindrop pattern over this fine debris."},   # printed 58 s late
             {'g': 1200, 's': 'Parker', 't': 'Copy that, Jack.'}]
    sync_to_tape(lines, segments, tape)
    assert lines[0]['g'] == 1100.0 and lines[1]['g'] == 1200
    # the short lines before it, printed late too, come back with it: where they're heard, or just before it
    said2 = "okay charlie ready to copy roger go ahead over battery c is thirty seven point zero and we got an entry pad if you are ready".split()
    segments, tape = _tape([(100 + 0.4 * k, w) for k, w in enumerate(said2)])
    lines = [{'g': 1165, 's': 'Armstrong', 't': 'Okay, Charlie. Ready to copy?'}, {'g': 1167, 's': 'Duke', 't': 'Hmm.'},
             {'g': 1170, 's': 'Armstrong', 't': 'Battery C is 37.0.'},
             {'g': 1175, 's': 'Duke', 't': "And we got an entry PAD if you are ready."}]
    sync_to_tape(lines, segments, tape)
    battery = 1100 + 0.4 * said2.index('battery')
    assert lines[0]['g'] == 1100.0 and lines[2]['g'] == pytest.approx(battery) and lines[3]['g'] == pytest.approx(1100 + 0.4 * said2.index('and'))
    assert 1100 < lines[1]['g'] < battery   # (the one not heard: between the lines heard either side of it)
    assert sorted(lines, key=lambda l: l['g'])[-1]['s'] == 'Duke'
    # a line's words in order but strewn over minutes of other talk aren't the line said early
    strewn = [(100, 'antares'), (100.4, 'this'), (100.8, 'is'), (101.2, 'houston'), (101.6, 'over')] \
        + [(110 + 0.5 * k, w) for k, w in enumerate('go ahead houston we would like the pre liftoff configuration okay stand by'.split())] \
        + [(160, 'how'), (160.4, 'do'), (160.8, 'you'), (161.2, 'read'), (161.6, 'that')]
    segments, tape = _tape(strewn)
    lines = [{'g': 1380, 's': 'Haise', 't': 'Antares, this is Houston. How do you read?'}]
    sync_to_tape(lines, segments, tape)
    assert lines[0]['g'] == 1380
    segments, tape = _tape([(100 + 0.4 * k, w) for k, w in enumerate(said)] + [(200, 'copy'), (200.4, 'that'), (200.8, 'jack')])
    short = [{'g': 1158, 's': 'Schmitt', 't': 'Okay, Houston. There is.'}]   # too short to be sure of that far off
    sync_to_tape(short, segments, tape)
    assert short[0]['g'] == 1158


def test_apollo_17_capcoms_are_looked_up_on_the_clock_from_liftoff():
    from aligner.common import MISSION, speaker_names
    MISSION['n'] = '17'
    try:
        name = speaker_names('17', [])
        # the orange soil, 142:46 from liftoff (145:26 on Mission Control's clock): Bob Parker has the moonwalk
        assert name({'speaker': 'CC', 'getSeconds': 142 * 3600 + 46 * 60 + 57}) == 'Parker'
        # after the first moonwalk, 122:19 from liftoff ("Thank you, Joe"): Joe Allen, whom the journal has from 124:5x on its clock
        assert name({'speaker': 'CC', 'getSeconds': 122 * 3600 + 19 * 60 + 55}) == 'Allen'
    finally:
        MISSION['n'] = '11'


# The announcer through a rest period: the recorder ran only while he spoke,
# so the hourly announcements sit back to back on the tape
MORE_SAID_TIMES = [
    ('This is Apollo Control at 65 hours.', [(65 * 3600, 'open')]),
    ("This is Apollo Control, it's 66 hours one minute, Apollo 15 at present time.", [(66 * 3600 + 60, 'open')]),
    ('This is Apollo Control Houston at 90 hours at 10 minutes down to the flight.', [(90 * 3600 + 600, 'open')]),
    ('At 67 hours, this Apollo Control.', [(67 * 3600, 'close')]),
    ('This is Apollo Control at 200 hours 53 minutes.', [(200 * 3600 + 53 * 60, 'open')]),      # (past 200 hours: Apollo 15, 16, 17)
    ('This is Apollo control at 113 hours, 53.', []),                                             # (minutes he didn't finish: not "on the hour")
    ('This is Mission Control Houston at 172 hours, 28 minutes.', [(172 * 3600 + 28 * 60, 'open')]),
    ('Apollo control Houston, now 175 hours at 31 minutes.', [(175 * 3600 + 31 * 60, 'open')]),
    ('The clock on the front screen of mission control here is showing a wake time 7 hours 22 minutes from now.', []),
    ('This is Apollo Control at 62 hours, 21 minutes. We have secured. At 62 hours, 22 minutes, this is Mission Control Houston.',
     [(62 * 3600 + 21 * 60, 'open'), (62 * 3600 + 22 * 60, 'close')]),
]


@pytest.mark.parametrize('text, expected', MORE_SAID_TIMES)
def test_every_time_the_announcer_gives(text, expected):
    from aligner.announcer import said_times
    assert [(s, kind) for _at, s, kind in said_times(text)] == expected


def test_announcements_back_to_back_on_the_tape_each_go_to_the_time_given():
    from aligner.announcer import find_announcer
    from aligner.common import MISSION
    MISSION['n'] = '15'
    words = _spoken((100, 'This is Apollo Control at 62 hours, 21 minutes. We have secured the voice communications with Apollo 15 now.'),
                    (108, 'At 62 hours, 22 minutes, this is Mission Control Houston.'),
                    (113, 'This is Apollo Control at 65 hours. The crew now about two and a half hours into their rest period.'),
                    (121, 'This is Apollo Control at 68 hours. All systems functioning normally on the spacecraft.'),
                    (128, 'At 68 hours, one minute, this is Apollo Control.'))
    start = 62 * 3600 + 21 * 60 + 20 - 100   # the tape piece is placed by his first announcement
    segments = [{'tape': 'T', 'from': 0, 'to': 200, 'get': start, 'rate': 1.0}]
    spans, over, said = find_announcer(segments, [], {'T': (words,)}, {'T': []})
    at = {l['t']: l['g'] for l in said}
    assert abs(at['This is Apollo Control at 62 hours, 21 minutes.'] - (62 * 3600 + 21 * 60 + 20)) <= 2      # stays where it was
    assert abs(at['This is Apollo Control at 65 hours.'] - (65 * 3600 + 20)) <= 2                              # each of the others out to its own hour
    assert abs(at['This is Apollo Control at 68 hours.'] - (68 * 3600 + 20)) <= 2
    assert at['At 68 hours, one minute, this is Apollo Control.'] > at['All systems functioning normally on the spacecraft.'] > at['This is Apollo Control at 68 hours.']
    assert len(spans) == 3 and len([s for s in segments if s.get('spoken')]) == 2
    # one announcement that runs on in step with its own clock isn't cut
    words = _spoken((100, 'This is Apollo Control at 62 hours, 21 minutes. We have secured the voice communications.'),
                    (160, 'At 62 hours, 22 minutes, this is Apollo Control.'))
    segments = [{'tape': 'T', 'from': 0, 'to': 200, 'get': start, 'rate': 1.0}]
    spans, over, said = find_announcer(segments, [], {'T': (words,)}, {'T': []})
    assert len(segments) == 1 and not any(s.get('spoken') for s in segments)


def test_apollo_14_capcoms_are_looked_up_as_the_journal_has_them():
    from aligner.common import MISSION, speaker_names
    MISSION['n'] = '14'   # (its journal keeps time from liftoff through the clock update: nothing to undo)
    try:
        # Fred Haise until 110:05; 40 minutes out, this would be Bruce McCandless, who took over then
        assert speaker_names('14', [])({'speaker': 'CC', 'getSeconds': 109 * 3600 + 45 * 60}) == 'Haise'
    finally:
        MISSION['n'] = '11'


def test_a_line_a_report_has_dealt_with_leaves_the_review_list(tmp_path, monkeypatch):
    from aligner import fixes as X
    from aligner.review import score_lines
    vocab = {'this', 'is', 'the', 'left', 'hand', 'bag', 'okay', 'you', 'have', 'it', 'page', 'before', 'update', 'and'}
    lines = [{'g': 1000, 's': 'Unknown', 't': '... circuit breaker.', 'a': 1},                     # the listener names the speaker
             {'g': 2000, 's': 'Collins', 't': 'Okay. You have it.'},                                # says it isn't on the recording
             {'g': 3000, 's': 'Irwin', 't': 'The lefthand m_dsection is bag 2.'},                   # corrects it: "lefthand" is NASA's word
             {'g': 4000, 's': 'Haise', 't': 'And the 2age before, yoor tonsorial,les update.', 'a': 1},   # names the speaker; the garble stays
             {'g': 5000, 's': 'Unknown', 't': 'Boy, I hope - I hope - -', 'a': 1}]                  # a question still put to the listener
    listed = lambda: sorted(lines[i]['g'] for _q, i, _why in score_lines(lines, [], {}, vocab))
    assert listed() == [1000, 3000, 4000, 5000]   # (the second isn't listed until it's marked unheard)
    f = tmp_path / 'fixes.json'
    f.write_text(json.dumps({'11': [{'g': 1000, 'speaker': 'Armstrong', 'text': '... circuit breaker.'},
                                    {'g': 2000, 'text': 'Okay. You have it.', 'unheard': True},
                                    {'g': 3000, 'from': 'm_dsection', 'to': 'midsection'},
                                    {'g': 4000, 'speaker': 'Mitchell', 'text': 'And the 2age before'},
                                    {'g': 5000, 'text': 'Boy, I hope', 'review': "Who's speaking?"}]}))
    monkeypatch.setattr(X, 'FIXES', f)
    assert X.apply_fixes('11', lines) == 5
    ranked = score_lines(lines, [], {}, vocab)
    assert [lines[i]['g'] for _q, i, _why in ranked] == [5000, 4000]          # the question first, then the line still garbled
    assert ranked[1][2] == '2 damaged words: 2age, tonsorial,les'            # ("yoor" may be a word: only the plain garble is named)


def test_a_row_with_no_word_in_it_is_junk(vocab):
    from aligner.ocr_repair import junk_row
    for text in ('ee .', 'J', 'eee', 'vee', 'wae', ',', '~ @', 'en nee', '0k_y.', 'H_?'):
        assert junk_row(text, vocab), text
    for text in ('Go.', 'No.', "That's it.", 'Al?', 'Okey-dokey.', 'Roger-Roger.', 'Cut-off.', 'S-BAND T/R, T/R.', 'ULLAGE.', 'P64',
                 'I -', "I'm ...", 'Ahh!', 'Uh-huh.', '108,285.1.', 'Fal - -', '- -', '...', '...?', '... )', '7 ***', '... REFSMMAT.',
                 '\u2018America.', 'bee oy', '_0TRAL.', '(_aughter)', 'uKay.', 'Lay\u201d H - ia A AY oe ae iy we : ano were the first aay Ana God said, "let there be'):
        assert not junk_row(text, vocab), text


def test_handwriting_after_the_last_sentence_goes(vocab):
    from aligner.ocr_repair import scrap_after_sentence as scrap
    assert scrap('Go ahead, Houston. Apollo 8 here. ( . aot, ifr “ Coe x Fp ga MON Tey aa you # 4 a', vocab) == 'Go ahead, Houston. Apollo 8 here.'
    assert scrap('Roger. Please be informed there is a Santa Claus. ASL y ST', vocab) == 'Roger. Please be informed there is a Santa Claus. ASL y ST'   # (codes in capitals: left for the review list)
    assert scrap('Houston, Apollo 8. Over. 1', vocab) == 'Houston, Apollo 8. Over. 1'   # (a figure is never a scrap: "Roger. 0.9.")
    assert scrap("Roger. We've got it. Over.", vocab) == "Roger. We've got it. Over."
    assert scrap('Roger. Going to P00 and to ACCEPT, Houston.', vocab) == 'Roger. Going to P00 and to ACCEPT, Houston.'
    assert scrap('Okay. We got 30 minutes to the burn.', vocab) == 'Okay. We got 30 minutes to the burn.'
    assert scrap('Stand by. - -', vocab) == 'Stand by. - -'
    assert scrap('Roger. Copy. 112:53:48.', vocab) == 'Roger. Copy. 112:53:48.'
    assert scrap("That's affirmative. Over. Say again, Jim?", vocab) == "That's affirmative. Over. Say again, Jim?"
    for kept in ('Roger. 0.9.', 'MARK it. YAW 1 -', 'Roger. LM/CM DELTA-P, 0.2.', 'Roger. And turning over a page to 60 hours. And - -',
                 "Apollo, Terre. Salute de l'Endeavour.", 'Roger. Good readb ack.', 'Ha, ha, ha. Ha, ha, ha.',
                 "Look at me carry it! I'm carrying it over my shoulder! Ha ha ha!", 'Umm. Now wa - what - wha -', '*** we go. Yea! It came open! Ha ha!',
                 "We're counting up to 34 hours 11 minutes and 50 seconds. 4, 3, 2, 1 -", 'Okay, Tony. Had one more. Okay - -', 'On page 2-17. AOS - -'):
        assert scrap(kept, vocab) == kept, kept
