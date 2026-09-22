import re, json, sys, time, bisect
import requests

TS_RE = re.compile(r'(\d{2,3}:\d{2}:\d{2})')
MP3_HREF_RE = re.compile(r'(?:src|href)="([^"]+\.mp3)"')
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')
TITLE_RE = re.compile(r'<title>(.*?)</title>', re.I | re.S)
H2_RE = re.compile(r'<h2>(.*?)</h2>', re.I | re.S)
BOILERPLATE_RE = re.compile(r'Your browser does not support the audio element\.?', re.I)

def clean(html_fragment):
    text = TAG_RE.sub(' ', html_fragment)
    text = (
        text.replace('&nbsp;', ' ')
        .replace('&amp;', '&')
        .replace('&quot;', '"')
        .replace('&#39;', "'")
        .replace('&deg;', '°')
    )
    return WS_RE.sub(' ', text).strip()

def page_title(html):
    m = H2_RE.search(html)
    if m:
        return clean(m.group(1))
    m = TITLE_RE.search(html)
    if m:
        return clean(m.group(1))
    return ''

def get_to_seconds(get):
    h, m, s = get.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def normalize_get(get_str):
    h, mi, se = get_str.split(':')
    return f"{int(h):03d}:{mi}:{se}"

FN_HMS_RE = re.compile(r'[a-z0-9]+_(\d{3})_(\d{2})_(\d{2})', re.I)
FN_7DIGIT_RE = re.compile(r'(\d{7})')

def derive_get_from_filename(url):
    """The archive's own filenames encode the clip's true start GET far more
    reliably than nearby transcript text does (e.g. a12a_000_52_39.mp3,
    a15_0001610.mp3, a12a.1151543.mp3, a15a1651703.mp3). Prefer it."""
    base = url.rsplit('/', 1)[-1]
    if '_t-' in base or '/t-' in base:
        # Pre-launch "T-minus" countdown clips — not on the GET clock at
        # all (GET 000:00:00 is liftoff), so they don't have a valid
        # non-negative GET and must not be mixed into the timeline.
        return None
    m = FN_HMS_RE.match(base)
    if m:
        return f"{m.group(1)}:{m.group(2)}:{m.group(3)}"
    m = FN_7DIGIT_RE.search(base)
    if m:
        d = m.group(1)
        return f"{d[0:3]}:{d[3:5]}:{d[5:7]}"
    return None

# ---------------------------------------------------------------------------
# Audio clip extraction (unchanged approach from earlier version)
# ---------------------------------------------------------------------------

def extract_clips(html, base_url, source_url, source_label):
    clips = []
    seen_positions = set()
    all_ts = list(TS_RE.finditer(html))
    for m in MP3_HREF_RE.finditer(html):
        url_frag = m.group(1)
        if url_frag in seen_positions:
            continue
        pos = m.start()
        before_ts = [t for t in all_ts if t.start() < pos and pos - t.start() <= 600]
        after_ts = [t for t in all_ts if t.start() > pos and t.start() - pos <= 150]
        candidate = None
        if before_ts and after_ts:
            b, a = before_ts[-1], after_ts[0]
            candidate = b if (pos - b.start()) <= (a.start() - pos) else a
        elif before_ts:
            candidate = before_ts[-1]
        elif after_ts:
            candidate = after_ts[0]

        full_url = url_frag if url_frag.startswith('http') else base_url + url_frag
        filename_get = derive_get_from_filename(full_url)

        if candidate is None and filename_get is None:
            continue

        if filename_get is not None:
            get_norm = filename_get
        else:
            get_norm = normalize_get(candidate.group(1))

        seen_positions.add(url_frag)
        clips.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'audioUrl': full_url,
            'sourceUrl': source_url,
            'sourceLabel': source_label,
        })
    return clips

AUDIOINDEX_SECTION_RE = re.compile(
    r'<li><a href="(\.\./[^"]+\.html)"[^>]*>([^<]+)</a></li>\s*<ul>', re.I
)
AUDIOINDEX_ITEM_RE = re.compile(
    r'<li><a href="[^"]*#(\w+)"[^>]*>([^<]*)</a>\s*MP3 Audio Clip\.?\s*'
    r'<a href="([^"]+\.mp3)">\s*\[([^\]]*)\]</a></li>',
    re.I,
)

def parse_audioindex(html, base_url, afj_base, mission_number):
    """Dedicated parser for the AFJ audioindex.html list format (only a12
    has one), which interleaves day-page section headers with per-clip
    <li> entries and sometimes GET ranges that would confuse the generic
    nearest-timestamp heuristic."""
    events = []
    for m in AUDIOINDEX_SECTION_RE.finditer(html):
        events.append((m.start(), 'section', m.group(1), clean(m.group(2))))
    for m in AUDIOINDEX_ITEM_RE.finditer(html):
        events.append((m.start(), 'item', m.group(1), m.group(2), m.group(3), m.group(4)))
    events.sort(key=lambda e: e[0])

    clips = []
    current_page, current_title = None, ''
    for ev in events:
        if ev[1] == 'section':
            _, _, href, title = ev
            current_page = href
            current_title = title
            continue
        _, _, anchor, label_text, mp3_href, duration = ev
        label_text = clean(label_text)
        ts_match = TS_RE.search(label_text)
        get_norm = normalize_get(ts_match.group(1)) if ts_match else '000:00:00'
        full_url = mp3_href if mp3_href.startswith('http') else base_url + mp3_href
        source_url = afj_base + current_page.lstrip('./') if current_page else base_url
        clips.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'audioUrl': full_url,
            'sourceUrl': f"{source_url}#{anchor}",
            'sourceLabel': f"Apollo {mission_number} Flight Journal — {current_title}",
        })
    return clips

# ---------------------------------------------------------------------------
# Transcript line extraction (new)
# ---------------------------------------------------------------------------

SPEAKER_CLEAN_RE = re.compile(r'\s*\((onboard|backup)\)\s*$', re.I)

def clean_speaker(raw):
    channel = 'air-to-ground'
    m = SPEAKER_CLEAN_RE.search(raw)
    if m and m.group(1).lower() == 'onboard':
        channel = 'onboard'
    speaker = SPEAKER_CLEAN_RE.sub('', raw).strip().rstrip(':').strip()
    return speaker, channel

# AFJ dialogue lines: div class is inconsistent (cc/onboard/unclassed all
# occur for ordinary dialogue), so match on structure — a <b> timestamp +
# speaker immediately inside a div — rather than trusting the class, and
# get the onboard/air-to-ground distinction from the "(onboard)" suffix on
# the speaker name instead.
AFJ_LINE_RE = re.compile(
    r'<div(?:\s+class="[a-z]*")?>(?:<a name="[^"]*"></a>)?'
    r'<b>(\d{2,3}:\d{2}:\d{2})\s*([^<:]*?):?\s*</b>(.*?)</div>',
    re.S,
)

# PAO ("Public Affairs Officer") blocks are prose narration with no speaker
# tag of their own, so they need the page's own anchor points to date them.
PAO_BLOCK_RE = re.compile(r'<div class="pao">(.*?)</div>', re.S)
ANCHOR_RE = re.compile(r'<a name="(\d{6,7})(?:audio)?">')

def extract_afj_lines(html):
    lines = []
    for m in AFJ_LINE_RE.finditer(html):
        get_str, speaker_raw, text_html = m.groups()
        if not speaker_raw.strip():
            continue
        text = BOILERPLATE_RE.sub('', clean(text_html)).strip()
        if not text:
            continue
        speaker, channel = clean_speaker(speaker_raw)
        get_norm = normalize_get(get_str)
        lines.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'speaker': speaker,
            'channel': channel,
            'text': text[:600],
        })

    anchors = [(m.start(), m.group(1)) for m in ANCHOR_RE.finditer(html)]
    for m in PAO_BLOCK_RE.finditer(html):
        text = BOILERPLATE_RE.sub('', clean(m.group(1))).strip()
        if not text:
            continue
        # nearest anchor at or before this block's own position
        get_digits = None
        for pos, digits in anchors:
            if pos > m.start():
                break
            get_digits = digits
        if get_digits is None:
            continue
        get_norm = normalize_get(f"{get_digits[:-4]}:{get_digits[-4:-2]}:{get_digits[-2:]}")
        lines.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'speaker': 'Mission Control',
            'channel': 'pao',
            'text': text[:600],
        })
    return lines

# ALSJ pages (no div wrapper): <b>HH:MM:SS</b> Speaker: text ... until the
# next <b>HH:MM:SS</b> marker.
ALSJ_LINE_START_RE = re.compile(
    r'<b>(\d{2,3}:\d{2}:\d{2})</b>\s*([A-Z][A-Za-z .()\'-]{1,40}?):', re.S
)

def extract_alsj_lines(html):
    starts = list(ALSJ_LINE_START_RE.finditer(html))
    lines = []
    for i, m in enumerate(starts):
        get_str, speaker_raw = m.groups()
        text_start = m.end()
        text_end = starts[i + 1].start() if i + 1 < len(starts) else min(len(html), text_start + 1000)
        text = BOILERPLATE_RE.sub('', clean(html[text_start:text_end])).strip()
        if not text:
            continue
        speaker, channel = clean_speaker(speaker_raw)
        get_norm = normalize_get(get_str)
        lines.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'speaker': speaker,
            'channel': channel,
            'text': text[:600],
        })
    return lines

# ---------------------------------------------------------------------------
# Merge clips + lines, fetch, mission tables
# ---------------------------------------------------------------------------

MAX_CLIP_SPAN_SECONDS = 50 * 60  # longest real clip seen so far is ~44 min

def attach_lines_to_clips(clips, lines):
    """Each clip 'owns' every transcript line from its own GET up to (but
    not including) the next clip's GET, matched globally by time — this
    only approximates true audio boundaries (a clip may run a bit short or
    long of the next clip's start) but is close enough for a synced
    transcript display. Capped at MAX_CLIP_SPAN_SECONDS so a long gap
    before the next clip (a quiet cruise stretch) doesn't attach hours of
    lines with offsets far beyond the clip's actual audio length."""
    clips_sorted = sorted(clips, key=lambda c: c['getSeconds'])
    starts = [c['getSeconds'] for c in clips_sorted]
    for c in clips_sorted:
        c['lines'] = []
    for line in sorted(lines, key=lambda l: l['getSeconds']):
        i = bisect.bisect_right(starts, line['getSeconds']) - 1
        if i < 0:
            continue
        clip = clips_sorted[i]
        offset = line['getSeconds'] - clip['getSeconds']
        if offset > MAX_CLIP_SPAN_SECONDS:
            continue
        clip['lines'].append({
            'get': line['get'],
            'offsetSeconds': offset,
            'speaker': line['speaker'],
            'channel': line['channel'],
            'text': line['text'],
        })
    return clips_sorted

def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"  retry {attempt} for {url}: {e}", file=sys.stderr)
            time.sleep(1)
    raise RuntimeError(f"failed to fetch {url}")

def scrape_afj_page(url, page, base_url, mission_number):
    html = fetch(url + page)
    title = page_title(html) or page
    label = f"Apollo {mission_number} Flight Journal — {title}"
    # hrefs on these day-pages already include the "audio/" segment
    # themselves (src="audio/a15_..."), so the base is just the page's own
    # directory — prepending 'audio/' here would double it.
    clips = extract_clips(html, url, url + page, label)
    lines = extract_afj_lines(html)
    return clips, lines, title

def scrape_alsj_page(url, page, base_url, mission_number):
    html = fetch(url + page)
    title = page_title(html) or page
    label = f"Apollo {mission_number} Lunar Surface Journal — {title}"
    clips = extract_clips(html, url, url + page, label)
    lines = extract_alsj_lines(html)
    return clips, lines, title

MISSIONS = {
    11: {
        'afj': 'ap11fj',
        'alsj': 'a11',
        'afj_pages': [
            '01launch.html', '02earth-orbit-tli.html', '03tde.html', '04nav-housekeep.html',
            '05day2-mcc.html', '06day2-tv.html', '07day2-laser.html',
            '08day3-africa-breakfast.html', '09day3-entering-eagle.html',
            '11day4-approach.html', '12day4-loi1.html', '13day4-tv-orbit.html',
            '14day4-loi2.html', '15day4-eagle-checkout.html', '16day5-landing-prep.html',
            '17day5-undock-doi.html', '19day6-rendezvs-dock.html',
            '20day6-reboard-lmjett.html', '21day6-tei.html', '22day7-leave-lsi.html',
            '23day7-tv-food-prep.html', '24day8-news-checks.html',
            '25day8-reentry-stowage.html', '26day9-approach-earth.html', '27day9-entry.html',
        ],
        'alsj_pages': [
            'a11.launch.html', 'a11.landing.html', 'a11.evaprep.html', 'a11.step.html',
            'a11.mobility.html', 'a11.posteva.html', 'a11.clsout.html', 'a11.postland.html',
        ],
    },
    13: {
        'afj': 'ap13fj',
        'alsj': None,
        'afj_pages': [
            '00crewchange.html', '01launch_ascent.html', '02earth_orbit_tli.html', '03tde.html',
            '04day1-end.html', '05day2-mcc2-tv.html', '07day3-before-the-storm.html',
            '08day3-problem.html', '10day3-free-return.html', '11day3-minimise-power.html',
            '12day4-approach-moon.html', '13day4-leaving-moon.html', '14day4-homeward.html',
            '17day5-thumpandsnowflakes.html', '18day5-feelingthecold.html',
            '19day5-themanualcoursecorrection.html', '20day5-wobblesandbursts.html',
            '21day5-batterycharge.html', '22day6-packingup.html',
            '23day6-thereactivationchecklist.html', '24day6-wornoutcrew.html',
            '25day6-thelastcoursecorrection.html', '26day6-servicemoduleseparation.html',
            '29day6-returnhome.html',
        ],
    },
    17: {
        'afj': 'ap17fj',
        'alsj': 'a17',
        'afj_pages': [
            '01_day01_launch.html', '02_day01_earth_orbit_tli.html', '03_day01_tde.html',
            '04_day01_human_weathersat.html', '05_day02_part1.html',
            '06_day02_part2_earthwatching.html', '07_day03_part1_mcc2.html',
            '08a_day03_part2_enter_lm.html', '08b_day03_part3_heat_flow.html',
            '09_day04_part1_clock_update.html', '10_day04_part2_light_flash.html',
            '11_day05_part1_approach_moon.html', '12_day05_part2_loi.html',
            '13_day05_part3_doi.html', '14_day05_part4.html', '15_day06_part1.html',
            '15a_day06_part1_csm.html', '16_day06_part2_landing_prep.html',
            '16a_day06_part2_csm.html', '17_day06_part3_solo_ops1.html',
            '18_day07_solo_ops2-pt1.html', '19_day07_solo_ops2-pt2.html',
            '20_day08_solo_ops3-pt1.html', '21_day08_solo_ops3-pt2.html',
            '22_day09_part1_solo_ops4.html',
        ],
        'alsj_pages': [
            'a17.launch.html', 'a17.landing.html', 'a17.eva1prep.html', 'a17.1ststep.html',
            'a17.alsepoff.html', 'a17.alsepdep.html', 'a17.deepcore.html', 'a17.clsout1.html',
            'a17.eva1post.html', 'a17.eva2wake.html', 'a17.eva2prep.html', 'a17.trvsta1.html',
            'a17.sta1.html', 'a17.trvsta2.html', 'a17.sta2.html', 'a17.trvlm1.html',
            'a17.clsout2.html', 'a17.eva2post.html', 'a17.eva3prep.html', 'a17.trvsta3.html',
            'a17.sta4.html', 'a17.trvsta4.html', 'a17.sta5.html', 'a17.trvsta5.html',
            'a17.sta6.html', 'a17.trvsta6.html', 'a17.sta7.html', 'a17.sta8.html',
            'a17.trvsta9.html', 'a17.sta9.html', 'a17.trvlm3.html', 'a17.clsout3.html',
            'a17.eva3post.html', 'a17.site.html', 'a17.outcam.html', 'a17.prepdi.html',
            'a17.homeward.html', 'a17.postland.html',
        ],
    },
    8: {
        'afj': 'ap08fj',
        'alsj': None,
        'afj_pages': [
            '01launch_ascent.html', '02earth_orbit_tli.html', '03day1_green_sep.html',
            '04day1_maroon.html', '05day1_black.html', '06day2_green.html',
            '07day2_maroon.html', '08day2_black.html', '09day3_green.html',
            '10day3_maroon.html', '11day3_black_approach.html', '12day3_lunar_encounter.html',
            '13day4_orbit1.html', '14day4_orbit2.html', '15day4_orbit3.html',
            '16day4_orbit4.html', '17day4_orbit5.html', '18day4_orbit6.html',
            '19day4_orbit7.html', '20day4_orbit8.html', '21day4_orbit9.html',
            '22a-day4_final_orbit.html', '22b-day4_tei.html', '23day4-5_black.html',
            '24day5_green.html', '25day5_maroon.html', '26day5-6_black.html',
            '27day6_green.html', '28day6_maroon.html', '29day6_reentry.html',
        ],
    },
    9: {
        'afj': 'ap09fj',
        'alsj': None,
        'afj_pages': [
            '000_preparations.html', '001_day01_launch.html', '002_day01_rev001.html',
            '003_day01_rev002.html', '004_day01_rev003.html', '005_day01_rev004.html',
            '006_day01_rev005.html', '007_day01_rev006.html', '008_day01_rev007.html',
        ],
    },
    10: {
        'afj': 'ap10fj',
        'alsj': None,
        'afj_pages': [
            'as10-day1-pt1.html', 'as10-day1-pt2-earthorbit-rev1.html',
            'as10-day1-pt3-earthorbit-rev2.html', 'as10-day1-pt4-tli-docking.html',
            'as10-day1-pt5-lmext-sivb-sep.html', 'as10-day1-pt6-housekeep-tv.html',
            'as10-day1-pt7-ptc-sleep.html', 'as10-day2-pt8.html', 'as10-day2-pt9.html',
            'as10-day3-pt10.html', 'as10-day3-pt11.html', 'as10-day4-pt12a.html',
            'as10-day4-pt12b.html', 'as10-day4-pt13.html', 'as10-day4-pt16.html',
            'as10-day5-pt19.html', 'as10-day5-pt20.html', 'as10-day6-pt24.html',
            'as10-day6-pt25.html', 'as10-day6-pt27.html', 'as10-day6-pt29-tei.html',
            'as10-day7-pt30.html', 'as10-day7-pt31.html', 'as10-day8-pt32.html',
            'as10-day8-pt33.html', 'as10-day9-pt34.html', 'as10-day9-pt35.html',
            'as10-day9-pt36-entry-splash.html',
        ],
    },
    12: {
        'afj': 'ap12fj',
        'alsj': 'a12',
        'afj_audioindex': True,
        'alsj_pages': [
            'a12.eva1prep.html', 'a12.eva1prelim.html', 'a12.tvtrbls.html', 'a12.alsepoff.html',
            'a12.alsepdep.html', 'a12.clsout1.html', 'a12.posteva1.html', 'a12.eva2prep.html',
            'a12.trvhead.html', 'a12.head_bench.html', 'a12.sharp.html', 'a12.halo.html',
            'a12.surveyor.html', 'a12.clsout2.html',
        ],
    },
    14: {
        'afj': 'ap14fj',
        'alsj': 'a14',
        'afj_pages': [
            '01_day1_launch.html', '02_day1_earth_orbit_tli.html', '03_day1_tde.html',
            '04_day1_settling_down.html', '05_day1_tv_ptc.html', '06_day2_mcc2.html',
            '07_day2_sportsnews.html', '08_day3_get_update.html', '09_day3_tvlm_house.html',
            '10_day4_wakeup_approaching_moon.html', '11_day4_mcc_4.html',
            '12_day4_checking_lm_eps.html', '13_day4_swing_behind_moon.html',
            '14_day4_loi_first_impressions.html', '15_day4_descent_orbit_insertion.html',
            '16_day4_orbiting_moon.html', '19_day5_troubleshooting_lm_computer.html',
            '21_day5_kitty_hawk_solo_2.html', '22_day6_kitty_hawk_solo_3.html',
            '26_day6_tei_resting.html', '27_day7_mcc5_navigation.html',
            '28_day7_demos_on_tv.html', '29_day8_coasting_home.html',
            '30_day8_flashing_lights_and_probe.html', '31_day8_press_conference_tv.html',
            '32_day8_probe_to_rest.html', '33_day9_last_wakeup.html', '35_postflight.html',
        ],
        'alsj_pages': [
            'a14.launch.html', 'a14.landing.html', 'a14.eva1prep.html', 'a14.actchk.html',
            'a14.alsepoff.html', 'a14.alsepdep.html', 'a14.eva1post.html', 'a14.eva2prep.html',
            'a14.tocone.html', 'a14.conegeo.html', 'a14.stafg.html', 'a14.trvstaf.html',
            'a14.clsout2.html', 'a14.eva2post.html', 'a14.postland.html',
        ],
    },
    15: {
        'afj': 'ap15fj',
        'alsj': 'a15',
        'afj_pages': [
            '01launch_to_earth_orbit.html', '02earth_orbit_tli.html', '03tde.html',
            '04troubleshoot_ptc.html', '05day2_checking_sps.html', '06day2_enter_lm.html',
            '07day3_flashing_lights.html', '08day3_leak_hilltop.html', '09day4_lunar_encounter.html',
            '10a-day4_lunar_orbit1-2.html', '10b-day4_doi-rest.html', '11day5_wakeup.html',
            '12a-day5_doi_trim.html', '12b-day5_lm_activation.html', '12c-day5_lm_undock.html',
            '12d-day5_csm_circ.html', '12e-day5_landing_prep.html', '13solo_ops1.html',
            '14solo_ops2.html', '15solo_ops3.html', '16solo_ops4.html', '17rndz_dock.html',
            '18tunnel_leak_lm_jett.html', '19a-day9_orbital_science.html', '19b-day9_orbital_science.html',
            '20a-day10_science-68-69.html', '20b-day10_science-70.html', '20c-day10_science-71.html',
            '20d-day10_science-72.html', '21a-day10_subsat.html', '21b-day10_tei.html',
            '22day10_homeward.html', '23a-day11_science-sphere.html', '23b-day11_worden_eva.html',
            '23c-day11_uv-photos-p23.html', '24a-day12_p23-uv-photos.html', '24b-day12_eclipse-presser.html',
            '24c-day12_p23-science.html', '25a-day13_approach-earth.html', '25b-day13_entry-splashdown.html',
        ],
        'alsj_pages': [
            'a15.launch.html', 'a15.landing.html', 'a15.eva1wake.html', 'a15.eva1prep.html',
            'a15.lrvload.html', 'a15.lrvdep.html', 'a15.trv1prep.html', 'a15.trvlm1.html',
            'a15.elbow.html', 'a15.elbowtrv.html', 'a15.trvsta2.html', 'a15.sta2.html',
            'a15.alsepoff.html', 'a15.alsepdep.html', 'a15.heatflow2.html', 'a15.clsout1.html',
            'a15.eva1post.html', 'a15.eva2wake.html', 'a15.eva2plan.html', 'a15.eva2prep.html',
            'a15.eva2prelim.html', 'a15.trvsta6.html', 'a15.sta6crtr.html', 'a15.sta6abv.html',
            'a15.trvsta6a.html', 'a15.sta6a.html', 'a15.spur.html', 'a15.trvlm2.html',
            'a15.sta8.html', 'a15.clsout2.html', 'a15.eva2post.html', 'a15.eva3prep.html',
            'a15.eva3prelim.html', 'a15.coreextract.html', 'a15.trvsta9.html', 'a15.sta9.html',
            'a15.rille.html', 'a15.sta10.html', 'a15.trvlm3.html', 'a15.clsout3.html',
            'a15.eva3post.html', 'a15.sevaprep.html', 'a15.seva.html', 'a15.postseva.html',
            'a15.postland.html', 'a15.summary.html', 'a15.crew.html', 'a15.fltplan.html',
        ],
    },
    16: {
        'afj': 'ap16fj',
        'alsj': 'a16',
        'afj_pages': [
            '01_Day1_Pt1.html', '02_Day1_Pt2.html', '03_Day1_Pt3.html', '04_Day1_Pt4.html',
            '05_Day1_Pt5.html', '06_Day2_Pt1.html', '07_Day2_Pt2.html', '08_Day3_Pt1.html',
            '09_Day3_Pt2.html', '10_Day4_Pt1.html', '11_Day4_Pt2.html', '12_Day4_Pt3.html',
            '13_Day5_Pt1.html', '14_Day5_Pt2.html', '15_Day5_pt3.html', '16_Day5_Pt4.html',
            '17_Day5_Pt5.html', '18_Day5_Pt6.html', '19_Day6_Pt1.html', '20_Day6_Pt2.html',
            '21_Day7.html', '22_Day8_Pt1.html', '23_Day8_Pt2.html', '24_Day9_Pt1.html',
            '25_Day9_Pt2.html', '26_Day10_Pt1.html', '27_Day10_Pt2.html', '28_Day11_Pt1.html',
            '29_Day11_Pt2.html', '30_Day12.html',
        ],
        'alsj_pages': [
            'a16.launch.html', 'a16.landing.html', 'a16.eva1wake.html', 'a16.eva1prep.html',
            'a16.lrvload.html', 'a16.lrvdep.html', 'a16.trvsta1.html', 'a16.sta1.html',
            'a16.trvlm1.html', 'a16.alsepoff.html', 'a16.heatflow.html', 'a16.deepcore.html',
            'a16.thumper.html', 'a16.clsout1.html', 'a16.eva1post.html', 'a16.eva2wake.html',
            'a16.eva2prelim.html', 'a16.eva2prep.html', 'a16.geoprep1.html', 'a16.trvsta2.html',
            'a16.sta2.html', 'a16.trvsta4.html', 'a16.sta4.html', 'a16.sta5.html',
            'a16.trv6to8.html', 'a16.sta6.html', 'a16.house_rock.html', 'a16.sta8.html',
            'a16.trvlm2.html', 'a16.clsout2.html', 'a16.eva2post.html', 'a16.eva3wake.html',
            'a16.eva3prelim.html', 'a16.eva3prep.html', 'a16.trvsta9.html', 'a16.sta9.html',
            'a16.sta10.html', 'a16.sta10prime.html', 'a16.window.html', 'a16.trvsta11.html',
            'a16.sta11.html', 'a16.trvsta13.html', 'a16.sta13.html', 'a16.trvlm3.html',
            'a16.clsout3.html', 'a16.eva3post.html', 'a16.postland.html', 'a16.vip.html',
        ],
    },
}

def scrape_mission(n):
    cfg = MISSIONS[n]
    afj_base = f"https://apollojournals.org/afj/{cfg['afj']}/"
    all_clips, all_lines = [], []

    if cfg.get('afj_audioindex'):
        print("  scraping AFJ audioindex...", file=sys.stderr)
        html = fetch(afj_base + 'audio/audioindex.html')
        all_clips.extend(parse_audioindex(html, afj_base + 'audio/', afj_base, n))
        # audioindex has no transcript text, so still walk the day pages for
        # lines — the audioindex's own section headers give us that page
        # list for free, in mission order, deduplicated.
        seen_pages = set()
        afj_pages = []
        for m in AUDIOINDEX_SECTION_RE.finditer(html):
            page = m.group(1).lstrip('./')
            if page not in seen_pages:
                seen_pages.add(page)
                afj_pages.append(page)
        for page in afj_pages:
            try:
                _, lines, title = scrape_afj_page(afj_base, page, afj_base, n)
                all_lines.extend(lines)
                print(f"  {page}: {len(lines)} lines  ({title})", file=sys.stderr)
            except Exception as e:
                print(f"  SKIP {page}: {e}", file=sys.stderr)
    else:
        for page in cfg['afj_pages']:
            try:
                clips, lines, title = scrape_afj_page(afj_base, page, afj_base, n)
                all_clips.extend(clips)
                all_lines.extend(lines)
                print(f"  {page}: {len(clips)} clips, {len(lines)} lines  ({title})", file=sys.stderr)
            except Exception as e:
                print(f"  SKIP {page}: {e}", file=sys.stderr)

    if cfg.get('alsj'):
        alsj_base = f"https://apollojournals.org/alsj/{cfg['alsj']}/"
        for page in cfg['alsj_pages']:
            try:
                clips, lines, title = scrape_alsj_page(alsj_base, page, alsj_base, n)
                all_clips.extend(clips)
                all_lines.extend(lines)
                print(f"  {page}: {len(clips)} clips, {len(lines)} lines  ({title})", file=sys.stderr)
            except Exception as e:
                print(f"  SKIP {page}: {e}", file=sys.stderr)

    # dedupe clips by audioUrl, keep first
    seen = set()
    deduped = []
    for c in all_clips:
        if c['audioUrl'] in seen:
            continue
        seen.add(c['audioUrl'])
        deduped.append(c)

    clips = attach_lines_to_clips(deduped, all_lines)
    print(f"TOTAL for {n}: {len(clips)} unique clips, {len(all_lines)} transcript lines", file=sys.stderr)
    return clips

if __name__ == '__main__':
    mission = int(sys.argv[1])
    clips = scrape_mission(mission)
    json.dump(clips, sys.stdout, indent=0)
