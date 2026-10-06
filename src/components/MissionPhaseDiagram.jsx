import { PHASES } from '../data/phases'
import { useGlobeArt } from '../lib/design'

// Where the crew are right now, as a cartoon: Earth and Moon inside the two
// loops of a figure-8, the loops being the orbits (parking orbit around
// Earth, lunar orbit around the Moon) and the crossing in the middle the
// coast out and back. The craft are drawn where they are for the phase
// playing, on the path and pointing along it. A narrative picture, not to
// scale.
//
// viewBox 240 x 120: Earth at (46, 60), Moon at (194, 60), crossing at (120, 60).
// The sprites (src/data/globeArt.js) are made by scripts/make_sprites.py and
// scripts/make_painted_craft.py.

const EARTH = { x: 46, y: 60, r: 24 }
const MOON = { x: 194, y: 60, r: 15 }

// Out of Earth orbit up and across the middle, around the Moon, back across
// the middle and home: one continuous figure-8.
// Each loop is 36 units out from its world's center and 30 above and below.
function loop(cx, side) {
  const x = (d) => cx + side * d   // (side -1: the loop's far side is to the left)
  return `C ${120 - side * -16} 38, ${x(-26)} 30, ${cx} 30 C ${x(22)} 30, ${x(36)} 44, ${x(36)} 60 C ${x(36)} 76, ${x(22)} 90, ${cx} 90 C ${x(-26)} 90, ${120 - side * -16} 82, 120 60`
}
const FIGURE_8 = `M 120 60 ${loop(EARTH.x, -1)} ${loop(MOON.x, 1)}`

// [image, width, height] in pixels, for the aspect ratio
// (the art, Earth, Moon and spacecraft, is the Design menu's choice: `craft`
// is its spacecraft row from src/data/globeArt.js)
// the craft's widths in the diagram (cartoon sizes, not to scale); the LM's
// ascent stage is 0.6 of its width. A style can change them (the painted
// Saturn V stands upright, so it's narrower for the same height).
const WIDE = { stack: 40, csm: 28, lm: 22, chutes: 26, saturn: 18 }
const wide = (craft, name) => (craft.wide && craft.wide[name]) || WIDE[name]

// A sprite `w` units wide centered at (x, y). The craft are drawn facing
// left (the CSM's nose, or the LM leading the docked stack); `dir` is the
// heading in degrees (0 = right, 90 = down). Heading rightward the sprite is
// mirrored rather than turned upside down. `turn` just rotates it.
function Sprite({ name, x, y, w, dir, turn, art, craft }) {
  const [src, pw, ph] = art || craft.sprites[name]
  const h = (w * ph) / pw
  let spin = ''
  if (dir != null) spin = Math.cos((dir * Math.PI) / 180) > 0 ? ` rotate(${dir}) scale(-1 1)` : ` rotate(${dir - 180})`
  else if (turn != null) spin = ` rotate(${turn})`
  return (
    <image href={src} x={-w / 2} y={-h / 2} width={w} height={h} transform={`translate(${x} ${y})${spin}`} className="pd-sprite" />
  )
}

function tall(craft, name, w) {
  const [, pw, ph] = craft.sprites[name]
  return (w * ph) / pw
}

// A point off Earth's surface: `angle` degrees round from its center (0 =
// right, -90 = top), `out` units above the ground.
function offEarth(angle, out) {
  const a = (angle * Math.PI) / 180
  return { x: EARTH.x + (EARTH.r + out) * Math.cos(a), y: EARTH.y + (EARTH.r + out) * Math.sin(a) }
}

// The Saturn V climbs 27 degrees right of vertical from just off the ground
// at Earth's upper right, so it rises out of the atmosphere. Its tail (the
// point in the sprite that goes on the ground: the cartoon's flame tips, the
// painted one's engines) is placed there, after the style's own tilt.
function launchPose(craft) {
  const ground = offEarth(-40, 1)
  const [, pw, ph] = craft.sprites.saturn
  const k = wide(craft, 'saturn') / pw
  const [tx, ty] = craft.launch.tail
  const t = (craft.launch.tilt * Math.PI) / 180
  const dx = (tx - pw / 2) * k
  const dy = (ty - ph / 2) * k
  const pose = { x: ground.x - (dx * Math.cos(t) - dy * Math.sin(t)), y: ground.y - (dx * Math.sin(t) + dy * Math.cos(t)) }
  return craft.launch.tilt ? { ...pose, turn: craft.launch.tilt } : pose
}

// Coming home under the parachutes, over the Pacific (the globe's left
// side), heat shield toward the water.
function splashdownPose(craft) {
  const angle = -132
  return { ...offEarth(angle, 1 + tall(craft, 'chutes', wide(craft, 'chutes')) / 2), turn: angle + 90 }
}

// Standing on the Moon's top: the y that puts a sprite's feet on the surface.
// The Moon curves away under the LM's side feet, so it sits into the curve
// (the front foot a little in front of the Moon) rather than perching on it.
function onMoon(craft, name, w) {
  const [, pw, ph] = craft.sprites[name]
  return MOON.y - MOON.r - (w * ph) / pw / 2 + 4
}

// What's drawn for each phase: the craft and where (positions and headings
// taken from the figure-8's curves). While the crew are split, each craft is
// labeled with its name and how many are aboard.
function scene(phase, craft, lunar) {
  const lmW = wide(craft, 'lm')
  const csmInOrbit = { x: 229, y: 53, dir: 75 } // on the lunar loop's right side, heading down
  switch (phase) {
    case 'launch':
      return { rocket: launchPose(craft) }
    case 'earth-orbit':
      // in parking orbit the LM is still stowed below the CSM, on the rocket's last stage
      return { csm: { x: 67, y: 32, dir: -169 } }
    case 'earth-orbit-docked':
    case 'spacewalk':
      // (Apollo 9: the docked stack stayed in Earth orbit)
      return { stack: { x: 67, y: 32, dir: -169 } }
    case 'lm-solo':
      // (Apollo 10: the Lunar Module flew down toward the Moon on its own and came back up;
      // Apollo 9: it flew off on its own in Earth orbit)
      if (lunar) return { csm: csmInOrbit, lm: { name: 'lm', x: MOON.x - 17, y: MOON.y - 22, w: lmW }, split: true }
      return { csm: { x: 67, y: 32, dir: -169 }, lm: { name: 'lm', x: 30, y: 22, w: lmW }, tagX: 110, split: true }
    case 'transit-to-moon':
      return { stack: { x: 143, y: 40, dir: -29 } }
    case 'lunar-orbit':
      return { stack: { x: 218, y: 37, dir: 37 } }
    case 'landing':
      return { csm: csmInOrbit, lm: { name: 'lm', x: MOON.x - 17, y: MOON.y - 22, w: lmW }, split: true }
    case 'surface':
      return { csm: csmInOrbit, lm: { name: 'lm', x: MOON.x - 1, y: onMoon(craft, 'lm', lmW), w: lmW }, split: true }
    case 'ascent':
      return {
        csm: csmInOrbit,
        lm: { name: 'lmAscent', x: MOON.x + 10, y: MOON.y - 32, w: lmW * 0.6 },
        left: { name: 'lmDescent', x: MOON.x - 1, y: onMoon(craft, 'lmDescent', lmW), w: lmW },
        split: true,
      }
    case 'transit-to-earth':
      return { csm: { x: 149, y: 83, dir: -157 } }
    case 'splashdown':
      return { chutes: splashdownPose(craft) }
    default:
      return { stack: { x: 143, y: 40, dir: -29 } }
  }
}

function lastName(full) {
  return full.split(' ').slice(-1)[0]
}

// Who's where, in words, when the crew are split up.
function whoWhere(phase, mission) {
  if (!mission?.crew || !mission.lmName) return null
  const [cdr, cmp, lmp] = mission.crew.map(lastName)
  if (phase === 'spacewalk') {
    return `${lmp} outside, on ${mission.lmName}'s porch · ${cmp} in ${mission.csmName}'s open hatch · ${cdr} in ${mission.lmName}`
  }
  if (phase === 'lm-solo') {
    const where = mission.events?.loi ? 'in lunar orbit' : 'both in Earth orbit'
    return `${cdr} & ${lmp} in ${mission.lmName}, flying on their own · ${cmp} in ${mission.csmName}, ${where}`
  }
  if (!['landing', 'surface', 'ascent'].includes(phase)) return null
  const where = { landing: 'descending to the Moon', surface: 'on the Moon', ascent: 'rising to meet the CSM' }[phase]
  return `${cdr} & ${lmp} in ${mission.lmName}, ${where} · ${cmp} in ${mission.csmName}, in lunar orbit`
}

export default function MissionPhaseDiagram({ phase, mission }) {
  const p = PHASES[phase] || PHASES['transit-to-moon']
  const hasLM = !mission || !!mission.lmName
  const craft = useGlobeArt('craft')
  const s = scene(phase, craft, !!mission?.events?.loi)
  // A mission without a Lunar Module (Apollo 8) flies the CSM alone throughout.
  const stack = s.stack ? (hasLM ? { stack: s.stack } : { csm: s.stack }) : {}
  const caption = whoWhere(phase, mission)
  const split = s.split && hasLM
  const earthArt = useGlobeArt('earth')
  const moonArt = useGlobeArt('moon')

  return (
    <div className="phase-diagram">
      <svg viewBox="0 14 240 88" role="img" aria-label={`Currently: ${p.label}${caption ? `. ${caption}` : ''}`}>
        <path d={FIGURE_8} className="pd-path" fill="none" />
        <Sprite art={earthArt.sprite} x={EARTH.x} y={EARTH.y} w={EARTH.r * 2} />
        <Sprite art={moonArt.sprite} x={MOON.x} y={MOON.y} w={MOON.r * 2} />

        <g className="pd-scene" key={phase}>
          {s.rocket && <Sprite craft={craft} name="saturn" w={wide(craft, 'saturn')} {...s.rocket} />}
          {stack.stack && <Sprite craft={craft} name="stack" w={wide(craft, 'stack')} {...stack.stack} />}
          {stack.csm && <Sprite craft={craft} name="csm" w={wide(craft, 'csm')} {...stack.csm} />}
          {s.csm && <Sprite craft={craft} name="csm" w={wide(craft, 'csm')} {...s.csm} />}
          {split && s.left && <Sprite craft={craft} {...s.left} />}
          {split && <Sprite craft={craft} {...s.lm} />}
          {s.chutes && <Sprite craft={craft} name="chutes" w={wide(craft, 'chutes')} {...s.chutes} />}
          {split && mission && (
            <>
              <text x={s.lm.x - s.lm.w / 2 - 2} y={s.lm.y + 1} className="pd-tag" textAnchor="end">
                {mission.lmName} · 2
              </text>
              <text x={s.tagX ?? 236} y={s.csm.y + 22} className="pd-tag" textAnchor="end">
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
