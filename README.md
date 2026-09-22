# Apollo Audio Archive

Key moments from the Apollo lunar missions, in the astronauts' own voices —
a companion to [Apollo in Real Time](https://apolloinrealtime.org/) (which
already covers Apollo 11, 13 & 17 second-by-second) for the other lunar
missions: 8, 9, 10, 12, 14, 15 and 16.

Apollo 12 and 15 are live with curated audio clips. The rest are placeholders
to be filled in the same way.

## Adding a mission

Mission data lives in `src/data/missions.js`. Each mission has a `status` of
`'available'` or `'coming-soon'`, and an array of `moments`. To bring a new
mission online, set its status to `'available'` and add moments:

```js
{
  id: 'unique-slug',
  get: '000:00:00',       // Ground Elapsed Time, HH:MM:SS
  title: 'Short title',
  description: 'A sentence or two of context.',
  audioUrl: 'https://...',      // direct link to an mp3
  sourceUrl: 'https://...',     // page with the full transcript
  sourceLabel: 'Where this clip is from',
}
```

Audio clips so far are sourced from the [Apollo Flight Journal and Apollo
Lunar Surface Journal](https://apollojournals.org/) — public-domain NASA
mission recordings, individually clipped and time-stamped by that project.
Each moment links back to its source page for the full transcript and
credit.

## Development

```sh
npm install
npm run dev      # local dev server
npm run build    # production build to dist/
npm run lint     # oxlint
```
