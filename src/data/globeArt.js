import earthCartoon from '../assets/sprites/earth.webp'
import moonCartoon from '../assets/sprites/moon.webp'
import earthPainted from '../assets/sprites/earth-painted.webp'
import moonPainted from '../assets/sprites/moon-painted.webp'

// The Earth and Moon art for the mission diagram, chosen in the Design menu
// (the first of each is the default). [image, width, height] as in the
// diagram's sprites; add a new style by adding a row.
export const GLOBE_ART = {
  earth: [
    { id: 'painted', label: 'Painted', sprite: [earthPainted, 256, 256] },
    { id: 'cartoon', label: 'Cartoon', sprite: [earthCartoon, 255, 256] },
  ],
  moon: [
    { id: 'painted', label: 'Painted', sprite: [moonPainted, 256, 250] },
    { id: 'cartoon', label: 'Cartoon', sprite: [moonCartoon, 256, 252] },
  ],
}
