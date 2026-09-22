# Apollo Audio Archive

Nearly the entire Apollo lunar missions, in the astronauts' own voices — a
companion to [Apollo in Real Time](https://apolloinrealtime.org/) (which
already covers Apollo 11, 13 & 17 second-by-second) for the other lunar
missions: 8, 9, 10, 12, 14, 15 and 16.

Apollo 12 (259 clips) and Apollo 15 (1,153 clips) are live, covering launch
through splashdown with a chronological, chaptered timeline and continuous
playback. The rest are placeholders to be filled in the same way.

## How the audio is sourced

Every clip is pulled from the [Apollo Flight Journal and Apollo Lunar
Surface Journal](https://apollojournals.org/) — a volunteer archive of
public-domain NASA mission recordings, individually clipped and
time-stamped by that project down to Ground Elapsed Time (GET). Nothing is
hand-picked or fabricated: `scripts/scrape.py` walks every day-page (Flight
Journal) and EVA-page (Surface Journal) for a mission, pulls out every
`<audio>`/`.mp3` reference, and derives each clip's GET from the archive's
own filename convention (e.g. `a12a_000_52_39.mp3`, `a15a1651703.mp3`),
which is more reliable than nearby transcript text. Each clip keeps a link
back to its source page for the full transcript and credit.

### Adding a mission

```sh
pip install requests
python3 scripts/scrape.py 12 > src/data/clips/apollo12.json   # example
```

The script currently knows the Apollo 12 and 15 page lists (see
`ALSJ12_PAGES`, `AFJ15_PAGES`, etc. in `scripts/scrape.py`). For a new
mission, add its day-page and EVA-page filenames the same way (check the
mission's index page on apollojournals.org, e.g. `/afj/ap14fj/` and
`/alsj/a14/`), run the script, and drop the output at
`src/data/clips/<id>.json`.

Then in `src/data/missions.js`, set the mission's `status` to `'available'`
and add `clipsFile` (matching the JSON filename), `clipCount`, and
optionally a few `highlights` (GET-second shortcuts into the timeline, for
quick-jump chips — grab exact `getSeconds` values from the generated JSON
rather than guessing them).

## Development

```sh
npm install
npm run dev      # local dev server
npm run build    # production build to dist/
npm run lint     # oxlint
```
