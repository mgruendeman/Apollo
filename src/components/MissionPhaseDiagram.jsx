import { PHASES } from '../data/phases'

// Where the crew are right now, as a cartoon: Earth and Moon inside the two
// loops of a figure-8, the loops being the orbits (parking orbit around
// Earth, lunar orbit around the Moon) and the crossing in the middle the
// coast out and back. The craft are drawn where they are for the phase
// playing. A narrative picture, not to scale.
//
// viewBox 240 x 120: Earth at (54, 60), Moon at (186, 60), crossing at (120, 60).

const EARTH = { x: 54, y: 60, r: 17 }
const MOON = { x: 186, y: 60, r: 12 }
const K = 1.6 // cartoon scale of the craft

// Out of Earth orbit up and across the middle, around the Moon, back across
// the middle and home: one continuous figure-8.
const FIGURE_8 = [
  'M 120 60 C 104 38, 80 30, 54 30 C 32 30, 18 44, 18 60 C 18 76, 32 90, 54 90 C 80 90, 104 82, 120 60',
  'C 136 38, 160 30, 186 30 C 208 30, 222 44, 222 60 C 222 76, 208 90, 186 90 C 160 90, 136 82, 120 60',
].join(' ')

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

// What's drawn for each phase: the craft and where. While the crew are
// split, each craft is labeled with its name and how many are aboard.
function scene(phase) {
  const csmInOrbit = { x: 221, y: 54, angle: 100 } // on the lunar loop, clear of the Moon's top
  switch (phase) {
    case 'launch':
      return { rocket: { x: EARTH.x, y: EARTH.y - EARTH.r + 1 } }
    case 'earth-orbit':
      return { stack: { x: 32, y: 35, angle: 215 } }
    case 'transit-to-moon':
      return { stack: { x: 143, y: 40, angle: -22 } }
    case 'lunar-orbit':
      return { stack: { x: 211, y: 37, angle: 35 } }
    case 'landing':
      return { csm: csmInOrbit, lm: { x: MOON.x - 12, y: MOON.y - 18 }, split: true }
    case 'surface':
      return { csm: csmInOrbit, lm: { x: MOON.x - 2, y: MOON.y - MOON.r - 5 }, split: true }
    case 'ascent':
      return { csm: csmInOrbit, lm: { x: MOON.x + 9, y: MOON.y - 21 }, split: true }
    case 'transit-to-earth':
      return { csm: { x: 149, y: 83, angle: 200 } }
    case 'splashdown':
      return { chutes: { x: EARTH.x + 24, y: EARTH.y + 2 } }
    default:
      return { stack: { x: 143, y: 40, angle: -22 } }
  }
}

function lastName(full) {
  return full.split(' ').slice(-1)[0]
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
  const hasLM = !mission || !!mission.lmName
  const s = scene(phase)
  // A mission without a Lunar Module (Apollo 8) flies the CSM alone throughout.
  const stack = s.stack ? (hasLM ? { stack: s.stack } : { csm: s.stack }) : {}
  const caption = whoWhere(phase, mission)
  const split = s.split && hasLM

  return (
    <div className="phase-diagram">
      <svg viewBox="0 14 240 88" role="img" aria-label={`Currently: ${p.label}${caption ? `. ${caption}` : ''}`}>
        <path d={FIGURE_8} className="pd-path" fill="none" />

        {/* a cartoon Earth: ocean and a couple of continents */}
        <circle cx={EARTH.x} cy={EARTH.y} r={EARTH.r} className="pd-earth" />
        <path d="M 44 50 q 6 -6 12 -2 q 3 4 -2 8 q -5 2 -4 7 q -5 1 -7 -4 q -2 -5 1 -9 z" className="pd-land" />
        <path d="M 58 62 q 6 -2 8 3 q 0 5 -5 8 q -4 -1 -4 -5 q -2 -3 1 -6 z" className="pd-land" />

        {/* a cartoon Moon with craters */}
        <circle cx={MOON.x} cy={MOON.y} r={MOON.r} className="pd-moon" />
        <circle cx={MOON.x - 4} cy={MOON.y - 1} r="2.6" className="pd-crater" />
        <circle cx={MOON.x + 4} cy={MOON.y + 4} r="1.9" className="pd-crater" />
        <circle cx={MOON.x + 2.5} cy={MOON.y - 6} r="1.2" className="pd-crater" />

        <g className="pd-scene" key={phase}>
          {s.rocket && <SaturnV {...s.rocket} />}
          {stack.stack && <Stack {...stack.stack} />}
          {stack.csm && <CSM {...stack.csm} />}
          {s.csm && <CSM {...s.csm} />}
          {split && <LM {...s.lm} />}
          {s.chutes && <Parachutes {...s.chutes} />}
          {split && mission && (
            <>
              <text x={s.lm.x - 11} y={s.lm.y + 1} className="pd-tag" textAnchor="end">
                {mission.lmName} · 2
              </text>
              <text x={236} y={s.csm.y + 22} className="pd-tag" textAnchor="end">
                {mission.csmName} · 1
              </text>
            </>
          )}
        </g>
      </svg>
      <p className="phase-label">{p.label}</p>
      {caption && <p className="phase-who">{caption}</p>}
    </div>
  )
}
