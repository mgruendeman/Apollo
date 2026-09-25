import { PHASES } from '../data/phases'

// Where the crew are right now, as a cartoon: Earth and Moon joined by the
// figure-8 free-return path (out across the middle, around the Moon's far
// side, back across the middle), with the craft and their crew drawn where
// they are for the phase playing. A narrative picture, not to scale.
//
// viewBox 240 x 120: Earth at (38, 60), Moon at (206, 60).

const EARTH = { x: 38, y: 60, r: 17 }
const MOON = { x: 206, y: 60, r: 10 }
const LUNAR_ORBIT = 17
const K = 1.6   // cartoon scale of the craft and crew

const OUTBOUND = 'M 52 49 C 86 36, 108 42, 122 60 C 136 78, 176 90, 204 79'
const AROUND = 'M 204 79 C 232 70, 232 50, 204 41'
const RETURN = 'M 204 41 C 176 30, 136 42, 122 60 C 108 78, 86 84, 52 71'

function lastName(full) {
  return full.split(' ').slice(-1)[0]
}

// A little astronaut: a white helmet with a dark visor.
function Crew({ x, y, n }) {
  return (
    <g className="pd-crew">
      {Array.from({ length: n }, (_, i) => {
        const cx = x + (i - (n - 1) / 2) * 5.6 * K
        return (
          <g key={i}>
            <circle cx={cx} cy={y} r={2.3 * K} className="pd-helmet" />
            <ellipse cx={cx + 0.5 * K} cy={y - 0.2 * K} rx={1.25 * K} ry={0.95 * K} className="pd-visor" />
          </g>
        )
      })}
    </g>
  )
}

// Command Module (cone) and Service Module (cylinder), pointing along +x.
function CSM({ x, y, angle = 0 }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${angle}) scale(${K})`} className="pd-craft">
      <rect x="-7" y="-2.4" width="6" height="4.8" rx="0.6" className="pd-sm" />
      <path d="M -1 -2.4 L 3.5 0 L -1 2.4 Z" className="pd-cm" />
      <path d="M -7 -1.4 L -9 -2.2 L -9 2.2 L -7 1.4 Z" className="pd-nozzle" />
    </g>
  )
}

// The Lunar Module: a gold box on four splayed legs.
function LM({ x, y, scale = 1 }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale * K})`} className="pd-craft">
      <path d="M -3.5 1 L -5.5 4.5 M 3.5 1 L 5.5 4.5" className="pd-legs" />
      <rect x="-3.5" y="-1.2" width="7" height="3" className="pd-lm-descent" />
      <path d="M -2.6 -1.2 L -2 -4 L 2 -4 L 2.6 -1.2 Z" className="pd-lm-ascent" />
    </g>
  )
}

// The docked stack: CSM nose to nose with the LM.
function Stack({ x, y, angle = 0 }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${angle})`}>
      <CSM x={-2 * K} y={0} />
      <g transform={`translate(${5.2 * K} 0) rotate(-90)`}>
        <LM x={0} y={0} scale={0.7} />
      </g>
    </g>
  )
}

function SaturnV({ x, y }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${K * 0.8})`} className="pd-craft">
      <path d="M -2 0 L -2 -13 L 0 -17 L 2 -13 L 2 0 Z" className="pd-rocket" />
      <path d="M -2 0 L -3.5 2 L 3.5 2 L 2 0 Z" className="pd-rocket-fins" />
      <path d="M -1.5 2.5 Q 0 8 1.5 2.5 Z" className="pd-flame" />
    </g>
  )
}

function Parachutes({ x, y }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${K * 0.9})`} className="pd-craft">
      {[-5, 0, 5].map((dx) => (
        <g key={dx}>
          <path d={`M ${dx - 3.2} -9 Q ${dx} -14 ${dx + 3.2} -9 Z`} className="pd-chute" />
          <path d={`M ${dx - 3} -9 L 0 -1 M ${dx + 3} -9 L 0 -1`} className="pd-lines" />
        </g>
      ))}
      <path d="M -2.5 2 L 0 -1.5 L 2.5 2 Z" className="pd-cm" />
    </g>
  )
}

// What's drawn for each phase: the craft, where, and who's aboard.
function scene(phase, hasLM) {
  const orbitTop = { x: MOON.x, y: MOON.y - LUNAR_ORBIT }
  const orbitRight = { x: MOON.x + 13, y: MOON.y - 11, angle: 230 }   // the CSM while the crew is split
  switch (phase) {
    case 'launch':
      return { rocket: { x: EARTH.x + 4, y: EARTH.y - EARTH.r + 1 }, crew: [{ x: EARTH.x + 24, y: EARTH.y - 30, n: 3 }] }
    case 'earth-orbit':
      return { stack: { x: EARTH.x + 16, y: EARTH.y - 20, angle: 30 }, crew: [{ x: EARTH.x + 22, y: EARTH.y - 34, n: 3 }] }
    case 'transit-to-moon':
      return { stack: { x: 160, y: 83, angle: 12 }, crew: [{ x: 162, y: 70, n: 3 }] }
    case 'lunar-orbit':
      return { stack: { ...orbitTop, angle: 180 }, crew: [{ x: orbitTop.x - 2, y: orbitTop.y - 12, n: 3 }] }
    case 'landing':
      return {
        csm: orbitRight,
        lm: { x: MOON.x - 13, y: MOON.y - 9 },
        crew: [{ x: orbitRight.x + 7, y: orbitRight.y - 10, n: 1 }, { x: MOON.x - 30, y: MOON.y - 14, n: 2 }],
      }
    case 'surface':
      return {
        csm: orbitRight,
        lm: { x: MOON.x - 3, y: MOON.y - MOON.r - 5.2 },
        crew: [{ x: orbitRight.x + 7, y: orbitRight.y - 10, n: 1 }, { x: MOON.x - 22, y: MOON.y - 18, n: 2 }],
      }
    case 'ascent':
      return {
        csm: orbitRight,
        lm: { x: MOON.x - 11, y: MOON.y - 12 },
        crew: [{ x: orbitRight.x + 7, y: orbitRight.y - 10, n: 1 }, { x: MOON.x - 28, y: MOON.y - 18, n: 2 }],
      }
    case 'transit-to-earth':
      return { csm: { x: 160, y: 37, angle: 190 }, crew: [{ x: 160, y: 25, n: 3 }] }
    case 'splashdown':
      return { chutes: { x: EARTH.x + 26, y: EARTH.y - 2 }, crew: [{ x: EARTH.x + 28, y: EARTH.y + 10, n: 3 }] }
    default:
      return hasLM ? { stack: { x: 160, y: 83, angle: 12 }, crew: [] } : { csm: { x: 160, y: 83, angle: 12 }, crew: [] }
  }
}

// Who's where, in words, when the crew are split up.
function whoWhere(phase, mission) {
  if (!mission?.crew || !mission.lmName || !['landing', 'surface', 'ascent'].includes(phase)) return null
  const [cdr, cmp, lmp] = mission.crew.map(lastName)
  const where = { landing: 'descending to the Moon', surface: 'on the Moon', ascent: 'rising to meet the CSM' }[phase]
  return `${cdr} & ${lmp} in ${mission.lmName}, ${where} · ${cmp} in ${mission.csmName}, in lunar orbit`
}

export default function MissionPhaseDiagram({ phase, mission }) {
  const p = PHASES[phase] || PHASES['transit-to-moon']
  const hasLM = !!mission?.lmName || !mission
  const s = scene(phase, hasLM)
  // Before the crews split, a mission without a Lunar Module (Apollo 8) flies the CSM alone.
  const stack = s.stack && !hasLM ? { csm: s.stack } : s.stack ? { stack: s.stack } : {}
  const caption = whoWhere(phase, mission)

  return (
    <div className="phase-diagram">
      <svg viewBox="0 16 240 92" role="img" aria-label={`Currently: ${p.label}${caption ? `. ${caption}` : ''}`}>
        <path d={OUTBOUND} className="pd-path" fill="none" />
        <path d={AROUND} className="pd-path" fill="none" />
        <path d={RETURN} className="pd-path" fill="none" />
        <path d="M 150 78 l 4 1.6 l -3.6 2" className="pd-arrow" fill="none" />
        <path d="M 150 42 l -4 -1.6 l 3.6 -2" className="pd-arrow" fill="none" />

        <circle cx={EARTH.x} cy={EARTH.y} r={EARTH.r + 7} className="pd-orbit" fill="none" />
        <circle cx={MOON.x} cy={MOON.y} r={LUNAR_ORBIT} className="pd-orbit" fill="none" />

        {/* a cartoon Earth: ocean, a couple of continents, a wisp of cloud */}
        <circle cx={EARTH.x} cy={EARTH.y} r={EARTH.r} className="pd-earth" />
        <path d="M 28 50 q 6 -6 12 -2 q 3 4 -2 8 q -5 2 -4 7 q -5 1 -7 -4 q -2 -5 1 -9 z" className="pd-land" />
        <path d="M 42 62 q 6 -2 8 3 q 0 5 -5 8 q -4 -1 -4 -5 q -2 -3 1 -6 z" className="pd-land" />
        <path d="M 26 66 q 8 -3 16 1" className="pd-cloud" fill="none" />

        {/* a cartoon Moon with craters */}
        <circle cx={MOON.x} cy={MOON.y} r={MOON.r} className="pd-moon" />
        <circle cx={MOON.x - 3} cy={MOON.y - 2} r="2.2" className="pd-crater" />
        <circle cx={MOON.x + 3.5} cy={MOON.y + 3} r="1.6" className="pd-crater" />
        <circle cx={MOON.x + 2} cy={MOON.y - 5} r="1" className="pd-crater" />

        <g className="pd-scene" key={phase}>
          {s.rocket && <SaturnV {...s.rocket} />}
          {stack.stack && <Stack {...stack.stack} />}
          {stack.csm && <CSM {...stack.csm} />}
          {s.csm && <CSM {...s.csm} />}
          {s.lm && hasLM && <LM {...s.lm} />}
          {s.chutes && <Parachutes {...s.chutes} />}
          {s.crew.map((c, i) => (
            <Crew key={i} {...c} />
          ))}
        </g>
      </svg>
      <p className="phase-label">{p.label}</p>
      {caption && <p className="phase-who">{caption}</p>}
    </div>
  )
}
