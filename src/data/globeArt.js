import earthCartoon from '../assets/sprites/earth.webp'
import moonCartoon from '../assets/sprites/moon.webp'
import earthPainted from '../assets/sprites/earth-painted.webp'
import moonPainted from '../assets/sprites/moon-painted.webp'
import stackCartoon from '../assets/sprites/stack.webp'
import csmCartoon from '../assets/sprites/csm.webp'
import lmCartoon from '../assets/sprites/lm.webp'
import lmAscentCartoon from '../assets/sprites/lm-ascent.webp'
import lmDescentCartoon from '../assets/sprites/lm-descent.webp'
import chutesCartoon from '../assets/sprites/chutes.webp'
import saturnCartoon from '../assets/sprites/saturn.webp'
import stackPainted from '../assets/sprites/stack-painted.webp'
import csmPainted from '../assets/sprites/csm-painted.webp'
import lmPainted from '../assets/sprites/lm-painted.webp'
import lmAscentPainted from '../assets/sprites/lm-ascent-painted.webp'
import lmDescentPainted from '../assets/sprites/lm-descent-painted.webp'
import chutesPainted from '../assets/sprites/chutes-painted.webp'
import saturnPainted from '../assets/sprites/saturn-painted.webp'

// The art for the mission diagram, chosen in the Design menu (the first of
// each kind is the default). Sprites are [image, width, height] in pixels;
// add a new style by adding a row. The spacecraft are drawn facing left
// (scripts/make_sprites.py, scripts/make_painted_craft.py).
export const ART = {
  earth: [
    { id: 'painted', label: 'Painted', thumb: earthPainted, sprite: [earthPainted, 256, 256] },
    { id: 'cartoon', label: 'Cartoon', thumb: earthCartoon, sprite: [earthCartoon, 255, 256] },
  ],
  moon: [
    { id: 'painted', label: 'Painted', thumb: moonPainted, sprite: [moonPainted, 256, 250] },
    { id: 'cartoon', label: 'Cartoon', thumb: moonCartoon, sprite: [moonCartoon, 256, 252] },
  ],
  craft: [
    {
      id: 'painted',
      label: 'Painted',
      thumb: lmPainted,
      sprites: {
        stack: [stackPainted, 256, 152],
        csm: [csmPainted, 256, 243],
        lm: [lmPainted, 256, 237],
        lmAscent: [lmAscentPainted, 256, 108],
        lmDescent: [lmDescentPainted, 256, 132],
        chutes: [chutesPainted, 172, 256],
        saturn: [saturnPainted, 93, 256],
      },
      // the Saturn V stands upright: its engines at the bottom middle, tilted
      // over by the diagram as it climbs
      launch: { tail: [46.5, 256], tilt: 27 },
      // (upright and with its antennas and chutes these stand taller: narrower)
      wide: { saturn: 11, chutes: 20, stack: 36 },
    },
    {
      id: 'cartoon',
      label: 'Cartoon',
      thumb: lmCartoon,
      sprites: {
        stack: [stackCartoon, 256, 86],
        csm: [csmCartoon, 256, 105],
        lm: [lmCartoon, 256, 214],
        lmAscent: [lmAscentCartoon, 256, 193],
        lmDescent: [lmDescentCartoon, 256, 97],
        chutes: [chutesCartoon, 256, 246],
        saturn: [saturnCartoon, 148, 256],
      },
      // drawn already leaning 27 degrees right, the tips of its flames here
      launch: { tail: [15, 253], tilt: 0 },
    },
  ],
}
