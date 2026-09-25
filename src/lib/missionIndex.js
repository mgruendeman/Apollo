import { PHASES } from '../data/phases'

// The site's own index of a mission: chapters by mission day and flight
// phase ("Day 3 · Translunar Coast"), not the source journals' page
// structure. Mission days are counted from liftoff, 24 hours each.
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

// The phase at a mission time, from the clip-based phase, corrected by the
// landing time the mission data gives (clips can lag the descent).
export function phaseAt(getSeconds, phase, landingSeconds) {
  if (landingSeconds && getSeconds >= landingSeconds - DESCENT_SECONDS && getSeconds < landingSeconds) return 'landing'
  if (landingSeconds && phase === 'landing' && getSeconds >= landingSeconds + 60) return 'surface'
  return phase
}

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
