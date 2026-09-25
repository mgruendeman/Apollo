import { PHASES } from '../data/phases'
import earthImg from '../assets/sprites/earth.webp'
import moonImg from '../assets/sprites/moon.webp'
import stackImg from '../assets/sprites/stack.webp'
import csmImg from '../assets/sprites/csm.webp'
import lmImg from '../assets/sprites/lm.webp'
import lmAscentImg from '../assets/sprites/lm-ascent.webp'
import lmDescentImg from '../assets/sprites/lm-descent.webp'
import chutesImg from '../assets/sprites/chutes.webp'
import saturnImg from '../assets/sprites/saturn.webp'

// Where the crew are right now, as a cartoon: Earth and Moon inside the two
// loops of a figure-8, the loops being the orbits (parking orbit around
// Earth, lunar orbit around the Moon) and the crossing in the middle the
// coast out and back. The craft are drawn where they are for the phase
// playing, on the path and pointing along it. A narrative picture, not to
// scale.
//
// viewBox 240 x 120: Earth at (54, 60), Moon at (186, 60), crossing at (120, 60).
// The sprites are made by scripts/make_sprites.py.

const EARTH = { x: 54, y: 60, r: 20 }
const MOON = { x: 186, y: 60, r: 15 }

// Out of Earth orbit up and across the middle, around the Moon, back across
// the middle and home: one continuous figure-8.
const FIGURE_8 = [
  'M 120 60 C 104 38, 80 30, 54 30 C 32 30, 18 44, 18 60 C 18 76, 32 90, 54 90 C 80 90, 104 82, 120 60',
  'C 136 38, 160 30, 186 30 C 208 30, 222 44, 222 60 C 222 76, 208 90, 186 90 C 160 90, 136 82, 120 60',
].join(' ')

// [image, width, height] in pixels, for the aspect ratio
const SPRITES = {
  earth: [earthImg, 255, 256],
  moon: [moonImg, 256, 252],
  stack: [stackImg, 256, 86],
  csm: [csmImg, 256, 105],
  lm: [lmImg, 256, 214],
  lmAscent: [lmAscentImg, 256, 193],
  lmDescent: [lmDescentImg, 256, 97],
  chutes: [chutesImg, 256, 246],
  saturn: [saturnImg, 148, 256],
}
// the craft's widths in the diagram (cartoon sizes, not to scale); the LM's
// ascent stage is 0.6 of its width
const WIDE = { stack: 40, csm: 28, lm: 22, chutes: 26, saturn: 18 }

// A sprite `w` units wide centered at (x, y). The craft are drawn facing
// left (the CSM's nose, or the LM leading the docked stack); `dir` is the
// heading in degrees (0 = right, 90 = down). Heading rightward the sprite is
// mirrored rather than turned upside down. `turn` just rotates it.
function Sprite({ name, x, y, w, dir, turn }) {
  const [src, pw, ph] = SPRITES[name]
  const h = (w * ph) / pw
  let spin = ''
  if (dir != null) spin = Math.cos((dir * Math.PI) / 180) > 0 ? ` rotate(${dir}) scale(-1 1)` : ` rotate(${dir - 180})`
  else if (turn != null) spin = ` rotate(${turn})`
  return (
    <image href={src} x={-w / 2} y={-h / 2} width={w} height={h} transform={`translate(${x} ${y})${spin}`} className="pd-sprite" />
  )
}

function tall(name, w) {
  const [, pw, ph] = SPRITES[name]
  return (w * ph) / pw
}

// A point off Earth's surface: `angle` degrees round from its center (0 =
// right, -90 = top), `out` units above the ground.
function offEarth(angle, out) {
  const a = (angle * Math.PI) / 180
  return { x: EARTH.x + (EARTH.r + out) * Math.cos(a), y: EARTH.y + (EARTH.r + out) * Math.sin(a) }
}

// The Saturn V as drawn climbs 27 degrees right of vertical, the tips of its
// flames at (15, 253) of its 148 x 256 pixels: those go just off the ground
// at Earth's upper right, so it rises out of the atmosphere.
function launchPose() {
  const tail = offEarth(-40, 1)
  const k = WIDE.saturn / 148
  return { x: tail.x + (74 - 15) * k, y: tail.y + (128 - 253) * k }
}

// Coming home under the parachutes, over the Pacific (the globe's left
// side), heat shield toward the water.
function splashdownPose() {
  const angle = -132
  return { ...offEarth(angle, 1 + tall('chutes', WIDE.chutes) / 2), turn: angle + 90 }
}

// Standing on the Moon's top: the y that puts a sprite's feet on the surface.
// The Moon curves away under the LM's side feet, so it sits into the curve
// (the front foot a little in front of the Moon) rather than perching on it.
function onMoon(name, w) {
  const [, pw, ph] = SPRITES[name]
  return MOON.y - MOON.r - (w * ph) / pw / 2 + 4
}

// What's drawn for each phase: the craft and where (positions and headings
// taken from the figure-8's curves). While the crew are split, each craft is
// labeled with its name and how many are aboard.
function scene(phase) {
  const csmInOrbit = { x: 221, y: 53, dir: 75 } // on the lunar loop's right side, heading down
  switch (phase) {
    case 'launch':
      return { rocket: launchPose() }
    case 'earth-orbit':
      // in parking orbit the LM is still stowed below the CSM, on the rocket's last stage
      return { csm: { x: 75, y: 32, dir: -169 } }
    case 'transit-to-moon':
      return { stack: { x: 143, y: 40, dir: -29 } }
    case 'lunar-orbit':
      return { stack: { x: 210, y: 37, dir: 37 } }
    case 'landing':
      return { csm: csmInOrbit, lm: { name: 'lm', x: MOON.x - 17, y: MOON.y - 22, w: WIDE.lm }, split: true }
    case 'surface':
      return { csm: csmInOrbit, lm: { name: 'lm', x: MOON.x - 1, y: onMoon('lm', WIDE.lm), w: WIDE.lm }, split: true }
    case 'ascent':
      return {
        csm: csmInOrbit,
        lm: { name: 'lmAscent', x: MOON.x + 10, y: MOON.y - 32, w: WIDE.lm * 0.6 },
        left: { name: 'lmDescent', x: MOON.x - 1, y: onMoon('lmDescent', WIDE.lm), w: WIDE.lm },
        split: true,
      }
    case 'transit-to-earth':
      return { csm: { x: 149, y: 83, dir: -157 } }
    case 'splashdown':
      return { chutes: splashdownPose() }
    default:
      return { stack: { x: 143, y: 40, dir: -29 } }
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
        <Sprite name="earth" x={EARTH.x} y={EARTH.y} w={EARTH.r * 2} />
        <Sprite name="moon" x={MOON.x} y={MOON.y} w={MOON.r * 2} />

        <g className="pd-scene" key={phase}>
          {s.rocket && <Sprite name="saturn" w={WIDE.saturn} {...s.rocket} />}
          {stack.stack && <Sprite name="stack" w={WIDE.stack} {...stack.stack} />}
          {stack.csm && <Sprite name="csm" w={WIDE.csm} {...stack.csm} />}
          {s.csm && <Sprite name="csm" w={WIDE.csm} {...s.csm} />}
          {split && s.left && <Sprite {...s.left} />}
          {split && <Sprite {...s.lm} />}
          {s.chutes && <Sprite name="chutes" w={WIDE.chutes} {...s.chutes} />}
          {split && mission && (
            <>
              <text x={s.lm.x - s.lm.w / 2 - 2} y={s.lm.y + 1} className="pd-tag" textAnchor="end">
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
