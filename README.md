# Apollo Audio Archive

Nearly the entire Apollo lunar missions, in the astronauts' own voices — a
companion to [Apollo in Real Time](https://apolloinrealtime.org/) (which
already covers Apollo 11, 13 & 17 second-by-second) for the other lunar
missions: 8, 9, 10, 12, 14, 15 and 16.

Six of those seven are live — Apollo 8, 10, 12, 14, 15 and 16 — each
covering launch through splashdown with:

- A chronological, chaptered timeline (thousands of clips total) with
  continuous auto-advance playback and lock-screen media controls
- A synced transcript that highlights the current line as the clip plays,
  with a colored badge per speaker
- A channel toggle where a clip has more than one: **Air-to-Ground** (the
  crew's radio calls to Houston), **Onboard** (hot-mic chatter never
  transmitted), and **Mission Control** (PAO narration)
- A schematic diagram showing roughly where the spacecraft is right now
  (earth orbit, translunar coast, lunar orbit, on the surface, etc.),
  classified from the source page's own title
- A glossary: jargon and hardware terms (GET, TLI, EECOM, PLSS, and more)
  are clickable right in the transcript, opening a panel with a fuller
  explanation and, where a real one exists, a quote from the people who
  were there
- A "happening right now" banner: if the current moment falls within a
  mission's real duration on its anniversary (same month/day/time, any
  later year), a banner on the home page — and a badge on that mission's
  page — links straight to that live GET

Apollo 9 has no digitized audio in the source archive yet, so it stays
"coming soon."

## How the audio is sourced

Every clip and transcript line is pulled from the [Apollo Flight Journal
and Apollo Lunar Surface Journal](https://apollojournals.org/) — a
volunteer archive of public-domain NASA mission recordings and
transcripts. Nothing is hand-written or fabricated:

- `scripts/scrape.py` walks every day-page (Flight Journal) and EVA-page
  (Surface Journal) for a mission, pulling out every `<audio>`/`.mp3`
  reference and every transcript line.
- Each clip's GET (Ground Elapsed Time) comes from the archive's own
  filename convention (e.g. `a12a_000_52_39.mp3`, `a15a1651703.mp3`),
  which is more reliable than nearby transcript text.
- Each transcript line's channel (air-to-ground / onboard / PAO) comes
  from the page's own markup (`<div class="cc/onboard/pao">` on Flight
  Journal pages) or the `(onboard)` suffix the archive puts on a
  speaker's name.
- Lines are attached to whichever clip's audio actually covers them (by
  GET, capped at 50 minutes so a long gap before the next clip doesn't
  drag in lines from hours later).

Every clip keeps a link back to its source page for the full transcript
and credit.

### Data layout

Each available mission has two files:

- `src/data/clips/<id>.json` — the lightweight clip index (get, audioUrl,
  sourceUrl, sourceLabel), imported eagerly when the mission page opens.
- `public/transcripts/<id>.json` — a map of clip id → transcript lines,
  fetched lazily as a static asset right after, so a multi-MB transcript
  file never blocks first paint.

### Adding a mission

```sh
pip install requests
python3 scripts/scrape.py 14   # writes JSON to stdout
```

`scripts/scrape.py` has a `MISSIONS` dict with each mission's AFJ/ALSJ
page lists (check the mission's index page on apollojournals.org, e.g.
`/afj/ap09fj/` and `/alsj/a14/`, to find them). Add an entry for the new
mission, run the script, then split its output into the two files above —
see the `process()` helper used to generate the existing missions (not
checked in as a script; it's a short loop over `scripts/scrape.py`'s
output that strips `lines` into the transcript file and re-adds a stable
`id` per clip from the audio filename).

Then in `src/data/missions.js`, set the mission's `status` to
`'available'` and add `clipsFile`, `clipCount`, and optionally a few
`highlights` (`{ id, title }`, using exact clip ids from the generated
JSON — matching by `getSeconds` alone can be ambiguous when two clips
share a timestamp).

### Other data files

- `src/data/glossary.js` — the term list for the clickable glossary.
  Definitions are written from general knowledge; a `quote` field is only
  ever a real, specific quote, not a paraphrase, and `links` only point
  at URLs that were actually verified to exist.
- `src/data/phases.js` — regex rules that classify a clip's source-page
  title into a rough mission phase (launch, translunar coast, lunar
  orbit, surface, etc.) for the diagram. It's a narrative aid, not a
  physically accurate trajectory.
- `src/lib/liveStatus.js` — the "years ago today" math. Each mission in
  `missions.js` carries `launchUtc` (verified launch time) and
  `durationSeconds` (verified mission duration); none of these six
  missions' real flights crossed a calendar year boundary, so only the
  current year's anniversary needs checking.

## Development

```sh
npm install
npm run dev      # local dev server
npm run build    # production build to dist/
npm run lint     # oxlint
```
