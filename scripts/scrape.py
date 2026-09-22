import re, json, sys, time
import requests

BASE_AFJ12 = "https://apollojournals.org/afj/ap12fj/"
BASE_AFJ15 = "https://apollojournals.org/afj/ap15fj/"
BASE_ALSJ12 = "https://apollojournals.org/alsj/a12/"
BASE_ALSJ15 = "https://apollojournals.org/alsj/a15/"

TS_RE = re.compile(r'(\d{2,3}:\d{2}:\d{2})')
BOILERPLATE_RE = re.compile(r'Your browser does not support the audio element\.?', re.I)
MP3_HREF_RE = re.compile(r'(?:src|href)="([^"]+\.mp3)"')
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')
TITLE_RE = re.compile(r'<title>(.*?)</title>', re.I | re.S)
H2_RE = re.compile(r'<h2>(.*?)</h2>', re.I | re.S)

def clean(html_fragment):
    text = TAG_RE.sub(' ', html_fragment)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    return WS_RE.sub(' ', text).strip()

def page_title(html):
    m = H2_RE.search(html)
    if m:
        return clean(m.group(1))
    m = TITLE_RE.search(html)
    if m:
        return clean(m.group(1))
    return ''

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

def get_to_seconds(get):
    h, m, s = get.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def extract_clips(html, base_url, source_url, source_label):
    clips = []
    seen_positions = set()
    all_ts = list(TS_RE.finditer(html))
    for m in MP3_HREF_RE.finditer(html):
        url_frag = m.group(1)
        if url_frag in seen_positions:
            continue
        pos = m.start()
        # nearest timestamp before (within 600 chars) or after (within 150 chars);
        # tight windows so we don't cross into a neighboring clip's own timestamp.
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

        # The filename's own encoded GET is authoritative and doesn't
        # require a nearby text match, so it's the only requirement for
        # inclusion; a missing/mismatched context window used to drop the
        # clip entirely even though we already know its real start time.
        if candidate is None and filename_get is None:
            continue

        if candidate is not None:
            get_str = candidate.group(1)
            h, mi, se = get_str.split(':')
            get_norm = f"{int(h):03d}:{mi}:{se}"
            # context: clean a generous raw window first, THEN truncate the
            # cleaned text — truncating the raw HTML instead risks cutting
            # off mid-tag and leaking an unclosed "<a href=..." fragment.
            ctx_start = candidate.start()
            raw_chunk = html[ctx_start:ctx_start + 500]
            context = BOILERPLATE_RE.sub('', clean(raw_chunk)).strip()
            if len(context) > 220:
                context = context[:217] + '...'
        else:
            get_norm = filename_get
            context = ''

        if filename_get is not None:
            get_norm = filename_get
        seen_positions.add(url_frag)
        clips.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'audioUrl': full_url,
            'context': context,
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

def parse_audioindex(html, base_url, afj_base):
    """Dedicated parser for the AFJ audioindex.html list format, which
    interleaves day-page section headers with per-clip <li> entries and
    sometimes GET ranges ("244:22:30 to 244:36:24") that would confuse the
    generic nearest-timestamp heuristic."""
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
        if ts_match:
            get_str = ts_match.group(1)
        else:
            # e.g. "T-Minus 17 sec " on the very first clip
            get_str = '000:00:00'
        h, mi, se = get_str.split(':')
        get_norm = f"{int(h):03d}:{mi}:{se}"
        full_url = mp3_href if mp3_href.startswith('http') else base_url + mp3_href
        source_url = afj_base + current_page.lstrip('./') if current_page else base_url
        clips.append({
            'get': get_norm,
            'getSeconds': get_to_seconds(get_norm),
            'audioUrl': full_url,
            'context': f"{label_text} [{duration}]".strip(),
            'sourceUrl': f"{source_url}#{anchor}",
            'sourceLabel': f"Apollo Flight Journal — {current_title}",
        })
    return clips

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

def scrape_pages(pages, base_url, page_label_prefix):
    all_clips = []
    for page in pages:
        url = base_url + page
        html = fetch(url)
        title = page_title(html) or page
        clips = extract_clips(html, base_url, url, f"{page_label_prefix} — {title}")
        print(f"  {page}: {len(clips)} clips  ({title})", file=sys.stderr)
        all_clips.extend(clips)
    return all_clips

AFJ12_PAGES = None  # filled from audioindex separately

ALSJ12_PAGES = [
    'a12.eva1prep.html','a12.eva1prelim.html','a12.tvtrbls.html','a12.alsepoff.html',
    'a12.alsepdep.html','a12.clsout1.html','a12.posteva1.html','a12.eva2prep.html',
    'a12.trvhead.html','a12.head_bench.html','a12.sharp.html','a12.halo.html',
    'a12.surveyor.html','a12.clsout2.html',
]

AFJ15_PAGES = [
    '01launch_to_earth_orbit.html','02earth_orbit_tli.html','03tde.html',
    '04troubleshoot_ptc.html','05day2_checking_sps.html','06day2_enter_lm.html',
    '07day3_flashing_lights.html','08day3_leak_hilltop.html','09day4_lunar_encounter.html',
    '10a-day4_lunar_orbit1-2.html','10b-day4_doi-rest.html','11day5_wakeup.html',
    '12a-day5_doi_trim.html','12b-day5_lm_activation.html','12c-day5_lm_undock.html',
    '12d-day5_csm_circ.html','12e-day5_landing_prep.html','13solo_ops1.html',
    '14solo_ops2.html','15solo_ops3.html','16solo_ops4.html','17rndz_dock.html',
    '18tunnel_leak_lm_jett.html','19a-day9_orbital_science.html','19b-day9_orbital_science.html',
    '20a-day10_science-68-69.html','20b-day10_science-70.html','20c-day10_science-71.html',
    '20d-day10_science-72.html','21a-day10_subsat.html','21b-day10_tei.html',
    '22day10_homeward.html','23a-day11_science-sphere.html','23b-day11_worden_eva.html',
    '23c-day11_uv-photos-p23.html','24a-day12_p23-uv-photos.html','24b-day12_eclipse-presser.html',
    '24c-day12_p23-science.html','25a-day13_approach-earth.html','25b-day13_entry-splashdown.html',
]

ALSJ15_PAGES = [
    'a15.launch.html','a15.landing.html','a15.eva1wake.html','a15.eva1prep.html',
    'a15.lrvload.html','a15.lrvdep.html','a15.trv1prep.html','a15.trvlm1.html',
    'a15.elbow.html','a15.elbowtrv.html','a15.trvsta2.html','a15.sta2.html',
    'a15.alsepoff.html','a15.alsepdep.html','a15.heatflow2.html','a15.clsout1.html',
    'a15.eva1post.html','a15.eva2wake.html','a15.eva2plan.html','a15.eva2prep.html',
    'a15.eva2prelim.html','a15.trvsta6.html','a15.sta6crtr.html','a15.sta6abv.html',
    'a15.trvsta6a.html','a15.sta6a.html','a15.spur.html','a15.trvlm2.html',
    'a15.sta8.html','a15.clsout2.html','a15.eva2post.html','a15.eva3prep.html',
    'a15.eva3prelim.html','a15.coreextract.html','a15.trvsta9.html','a15.sta9.html',
    'a15.rille.html','a15.sta10.html','a15.trvlm3.html','a15.clsout3.html',
    'a15.eva3post.html','a15.sevaprep.html','a15.seva.html','a15.postseva.html',
    'a15.postland.html','a15.summary.html','a15.crew.html','a15.fltplan.html',
]

if __name__ == '__main__':
    mission = sys.argv[1]
    if mission == '12':
        print("scraping AFJ12 audioindex...", file=sys.stderr)
        html = fetch(BASE_AFJ12 + 'audio/audioindex.html')
        afj_clips = parse_audioindex(html, BASE_AFJ12 + 'audio/', BASE_AFJ12)
        print(f"  audioindex: {len(afj_clips)} clips", file=sys.stderr)
        print("scraping ALSJ12 pages...", file=sys.stderr)
        alsj_clips = scrape_pages(ALSJ12_PAGES, BASE_ALSJ12, "Apollo 12 Lunar Surface Journal")
        all_clips = afj_clips + alsj_clips
    elif mission == '15':
        print("scraping AFJ15 pages...", file=sys.stderr)
        afj_clips = scrape_pages(AFJ15_PAGES, BASE_AFJ15, "Apollo 15 Flight Journal")
        print("scraping ALSJ15 pages...", file=sys.stderr)
        alsj_clips = scrape_pages(ALSJ15_PAGES, BASE_ALSJ15, "Apollo 15 Lunar Surface Journal")
        all_clips = afj_clips + alsj_clips
    else:
        raise SystemExit("usage: scrape.py <12|15>")

    # dedupe by audioUrl, keep first
    seen = set()
    deduped = []
    for c in all_clips:
        if c['audioUrl'] in seen:
            continue
        seen.add(c['audioUrl'])
        deduped.append(c)
    deduped.sort(key=lambda c: c['getSeconds'])
    print(f"TOTAL for {mission}: {len(deduped)} unique clips", file=sys.stderr)
    json.dump(deduped, sys.stdout, indent=2)
