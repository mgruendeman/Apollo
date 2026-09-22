// Classifies a clip/chapter into a rough mission phase from its source
// page title, for the schematic "where are they right now" diagram. This
// is intentionally approximate — a narrative aid, not a physically
// accurate trajectory — derived from the Flight/Surface Journal's own
// chapter naming, which is consistent enough across all missions to
// pattern-match reliably.
//
// Coordinates are in the diagram's 200x100 viewBox: Earth is centered at
// (26, 50) with an orbit ring at r=18; the Moon is centered at (174, 50)
// with an orbit ring at r=12.

export const PHASES = {
  launch: { label: 'Launch', x: 34, y: 60 },
  'earth-orbit': { label: 'Earth Orbit', x: 40, y: 35 },
  'transit-to-moon': { label: 'Translunar Coast', x: 100, y: 16 },
  'lunar-orbit': { label: 'Lunar Orbit', x: 165, y: 39 },
  landing: { label: 'Descent to the Surface', x: 178, y: 58 },
  surface: { label: 'On the Lunar Surface', x: 178, y: 52 },
  ascent: { label: 'Ascent & Rendezvous', x: 165, y: 42 },
  'transit-to-earth': { label: 'Transearth Coast', x: 100, y: 84 },
  splashdown: { label: 'Splashdown', x: 30, y: 62 },
}

const RULES = [
  ['splashdown', /entry|splashdown|re-?entry|recovery|homecoming|homeward.*(splash)/i],
  ['transit-to-earth', /trans-?earth|\btei\b|coasting home|homeward/i],
  ['ascent', /ascent from|lift-?off.*(surface|moon)|rendezvous|lm jettison|tunnel leak/i],
  ['surface', /\beva\b|surface|alsep|traverse|station \d|crater|rille|hadley|lunar roving|\blrv\b|regolith|core (tube|sample)|closeout/i],
  ['landing', /powered descent|descent and landing|\bpdi\b|landing\b/i],
  ['lunar-orbit', /lunar orbit|\bloi\b|descent orbit|\bdoi\b|circulariz|lunar encounter|orbiting the moon|acclimatising/i],
  ['transit-to-moon', /translunar|trans-lunar|\btli\b|transposition|extraction|passive thermal|barbecue|cislunar|solo ops/i],
  ['earth-orbit', /earth orbit/i],
  ['launch', /launch|lift-?off|reaching earth orbit|ascent to earth orbit/i],
]

export function classifyPhase(sourceLabel) {
  for (const [phase, re] of RULES) {
    if (re.test(sourceLabel)) return phase
  }
  return /Lunar Surface Journal/.test(sourceLabel) ? 'surface' : 'transit-to-moon'
}
