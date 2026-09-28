# Apollo Rewind

The Apollo Moon missions in the astronauts' own voices, at
[apollorewind.com](https://apollorewind.com).

- **Apollo 11, 12 and 14** play end to end from NASA's own tapes (the
  broadcast air-to-ground recordings on archive.org), with NASA's
  air-to-ground transcript timed to them and repaired from the tapes. The
  pipeline that builds them is in `pipeline/` (see `pipeline/README.md`);
  the site reads `public/timeline/apolloNN.json`. Their phases and chapters
  come from NASA's event times (`events` in `src/data/missions.js`).
- **Apollo 8, 10, 13, 15, 16 and 17**, until their tapes are done, play
  clips from the Apollo Flight Journal and Apollo Lunar Surface Journal,
  as described below. Once a mission moves to the tapes, its journal
  files move to `data/journal/` (the pipeline still reads the journal's
  CapCom names from them) and the site stops shipping them.
- **Apollo 9** lists NASA's recordings on archive.org.

## How the clip missions are sourced

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
  `durationSeconds` (verified mission duration); none of these missions'
  real flights crossed a calendar year boundary, so only the current
  year's anniversary needs checking.

## Development

```sh
npm install
npm run dev      # local dev server
npm run build    # production build to dist/
npm run lint     # oxlint
```
