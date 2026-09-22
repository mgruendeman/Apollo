import { stripSourcePrefix } from '../lib/sourceLabel'

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

// Orbit insertion happened roughly 11.5 minutes after liftoff on every
// Saturn V flight, and the journals title their first pages after where
// the flight ends up ("Launch and Reaching Earth Orbit"), so anything this
// early is still the climb, whatever the page title says.
const ORBIT_INSERTION_SECONDS = 11 * 60 + 30

// Every mission's translunar injection burn came within 3.5 hours of launch.
const LATEST_TLI_SECONDS = 3.5 * 3600

// Journal pages like "Awake on Splashdown day" start hours before entry.
const SPLASHDOWN_WINDOW_SECONDS = 2 * 3600

const RULES = [
  ['splashdown', /splashdown|recovery|homecoming/i],
  ['transit-to-earth', /trans-?earth|\btei\b|coasting home|homeward|going back/i],
  ['ascent', /ascent from|lift-?off.*(surface|moon)|return to orbit|rendezvous|lm jettison|tunnel leak/i],
  ['surface', /\beva\b|surface|alsep|traverse|station \d|crater|rille|hadley|lunar roving|\blrv\b|regolith|core (tube|sample)|closeout/i],
  ['landing', /powered descent|descent and landing|\bpdi\b|(?<!post-)(?<!for )landing\b/i],
  ['lunar-orbit', /lunar orbit|\bloi\b|descent orbit|\bdoi\b|circulariz|orbiting the moon|acclimatising/i],
  ['earth-orbit', /earth orbit|launch|lift-?off/i],
  ['transit-to-moon', /translunar|trans-lunar|\btli\b|transposition|extraction|passive thermal|barbecue|cislunar/i],
]

// Coarse mission stages, in flight order. Lunar orbit, landing, surface and
// ascent share a stage because the journals interleave CSM-only pages with
// surface pages while both are happening at once.
const STAGE = {
  launch: 0,
  'earth-orbit': 1,
  'transit-to-moon': 2,
  'lunar-orbit': 3,
  landing: 3,
  surface: 3,
  ascent: 3,
  'transit-to-earth': 4,
  splashdown: 5,
}

function matchLabel(label) {
  const title = stripSourcePrefix(label)
  for (const [phase, re] of RULES) {
    if (re.test(title)) return phase
  }
  return /Lunar Surface Journal/.test(label) ? 'surface' : null
}

// Many page titles don't name a phase ("The Maroon Team", "TV from Orbit",
// "Solo operations"), and a few clips from an earlier page are interleaved
// later by GET. So an unrecognized title carries the previous phase
// forward, and the flight never steps back to an earlier stage.
export function computePhases(clips, durationSeconds) {
  const phases = []
  let current = 'launch'
  for (const clip of clips) {
    let phase = clip.getSeconds < ORBIT_INSERTION_SECONDS ? 'launch' : matchLabel(clip.sourceLabel)
    if (phase === 'splashdown' && durationSeconds - clip.getSeconds > SPLASHDOWN_WINDOW_SECONDS) {
      phase = 'transit-to-earth'
    }
    if (!phase || STAGE[phase] < STAGE[current]) phase = current
    if (phase === 'earth-orbit' && clip.getSeconds > LATEST_TLI_SECONDS) phase = 'transit-to-moon'
    if (phase === 'launch' && clip.getSeconds >= ORBIT_INSERTION_SECONDS) phase = 'earth-orbit'
    phases.push(phase)
    current = phase
  }
  return phases
}
