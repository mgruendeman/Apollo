import { PHASES } from '../data/phases'

// The site's own index of a mission: chapters by mission day and flight
// phase ("Day 3 · Translunar Coast"). Mission days are counted from
// liftoff, 24 hours each. A tape mission's phases come from NASA's event
// times (tapeChapters); a clip mission's from its clips (buildChapters).
//
// While the crew is split between the Moon and lunar orbit, clips from the
// orbiting CSM are interleaved with the surface ones; they stay in the
// chapter of the stay (landing, surface or ascent) rather than breaking it
// into slivers.

const DAY = 24 * 3600
const SPLIT = new Set(['landing', 'surface', 'ascent'])
// Liftoff from the Moon to docking and casting off the LM took a few hours;
// after that the CSM is simply in lunar orbit again until the burn for home.
const ASCENT_HOURS = 5

// Powered descent to touchdown took about 12 minutes on every landing.
const DESCENT_SECONDS = 13 * 60

export function chapterTitle(getSeconds, phase) {
  return `Day ${missionDay(getSeconds)} · ${PHASES[phase]?.label || phase}`
}

export function missionDay(getSeconds) {
  return Math.max(1, Math.floor(getSeconds / DAY) + 1)
}

// Chapters: [{ title, phase, day, startIndex, endIndex }] over clips, whose
// phases (computePhases) are given in step.
export function buildChapters(clips, rawPhases) {
  const ascentFrom = clips[rawPhases.indexOf('ascent')]?.getSeconds
  const phases = rawPhases.map((p, i) =>
    p === 'ascent' && clips[i].getSeconds > ascentFrom + ASCENT_HOURS * 3600 ? 'lunar-orbit' : p,
  )
  const firstSplit = phases.findIndex((p) => SPLIT.has(p))
  let lastSplit = -1
  for (let i = phases.length - 1; i >= 0; i--) {
    if (SPLIT.has(phases[i])) {
      lastSplit = i
      break
    }
  }
  const chapters = []
  let stay = null // the split-phase a CSM-only clip belongs with
  for (let i = 0; i < clips.length; i++) {
    let phase = phases[i] || 'transit-to-moon'
    if (i >= firstSplit && i <= lastSplit && firstSplit >= 0) {
      if (SPLIT.has(phase)) stay = phase
      else if (phase === 'lunar-orbit' && stay) phase = stay
    }
    const day = missionDay(clips[i].getSeconds)
    const last = chapters[chapters.length - 1]
    if (last && last.phase === phase && last.day === day) {
      last.endIndex = i + 1
    } else {
      chapters.push({ phase, day, startIndex: i, endIndex: i + 1, title: `Day ${day} · ${PHASES[phase]?.label || phase}` })
    }
  }
  return chapters
}

// A mission time written "hhh:mm:ss" (or "-hhh:mm:ss") in seconds.
export function parseGet(get) {
  const neg = get.startsWith('-')
  const [h, m, s] = get.replace('-', '').split(':').map(Number)
  return (neg ? -1 : 1) * (h * 3600 + m * 60 + s)
}

// Earth orbit insertion came about 11.5 minutes after liftoff on every
// Saturn V flight.
const ORBIT_INSERTION_SECONDS = 11 * 60 + 30

// The flight phase at a mission time on a tape mission, from its events
// (missions.js): NASA's times for each burn, the landing and liftoff.
export function tapePhaseAt(mission, g) {
  const e = mission.events
  const at = (k) => parseGet(e[k])
  if (g < ORBIT_INSERTION_SECONDS) return 'launch'
  if (g < at('tli')) return 'earth-orbit'
  if (g < at('loi')) return 'transit-to-moon'
  if (mission.landingSeconds != null) {
    if (g < mission.landingSeconds - DESCENT_SECONDS) return 'lunar-orbit'
    if (g < mission.landingSeconds + 60) return 'landing'
    if (g < at('liftoff')) return 'surface'
    if (g < at('lmJettison')) return 'ascent'
  }
  // (Apollo 8 went into lunar orbit and came home: no landing between the two burns)
  if (g < at('tei')) return 'lunar-orbit'
  if (g < at('cmSep')) return 'transit-to-earth'
  return 'splashdown'
}

// A tape mission's chapters, by mission day and flight phase, over
// [from, to]: [{ title, phase, day, from, to }].
export function tapeChapters(mission, from, to) {
  const cuts = new Set([from, to, ORBIT_INSERTION_SECONDS])
  if (mission.landingSeconds != null) cuts.add(mission.landingSeconds - DESCENT_SECONDS).add(mission.landingSeconds + 60)
  for (const get of Object.values(mission.events)) cuts.add(parseGet(get))
  for (let d = DAY; d < to; d += DAY) cuts.add(d)
  const sorted = [...cuts].filter((c) => c >= from && c <= to).sort((a, b) => a - b)
  const chapters = []
  for (let i = 0; i + 1 < sorted.length; i++) {
    const a = sorted[i], b = sorted[i + 1]
    const phase = tapePhaseAt(mission, a)
    const day = missionDay(a)
    const last = chapters[chapters.length - 1]
    // (a phase running a few minutes past midnight stays in the day it began)
    if (last && last.phase === phase && (last.day === day || b - a < 3600)) last.to = b
    else chapters.push({ phase, day, from: a, to: b, title: `Day ${day} · ${PHASES[phase]?.label || phase}` })
  }
  return chapters
}
