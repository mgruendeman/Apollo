import { useEffect, useState, useSyncExternalStore } from 'react'
import { ART } from '../data/globeArt'

// The site's designs, to try side by side before settling on one. The
// choice is this browser's own (localStorage); index.html applies it before
// the page draws, so it doesn't flash the default first. Colors live in
// index.css under :root[data-design=...].
export const DESIGNS = [
  { id: 'classic', label: 'Classic', note: 'Navy and orange', swatch: ['#05070d', '#0d1220', '#ff8a3d', '#e8ecf6'] },
  { id: 'rewind', label: 'Rewind', note: 'The logo’s sunset on black', swatch: ['#0b0806', '#ffb52e', '#ff6a13', '#fbf6eb'] },
  { id: 'daylight', label: 'Rewind Daylight', note: 'Cream and sunset, light', swatch: ['#f6eddc', '#fffaf0', '#d6470e', '#1f1711'] },
]
const KEY = 'apollo-design'

export function currentDesign() {
  const d = document.documentElement.dataset.design
  return DESIGNS.some((x) => x.id === d) ? d : 'classic'
}

export function useDesign() {
  const [design, setDesignState] = useState(currentDesign)
  useEffect(() => {
    document.documentElement.dataset.design = design
    try {
      localStorage.setItem(KEY, design)
    } catch {
      /* just for this visit */
    }
  }, [design])
  return [design, setDesignState]
}

// The diagram's art (src/data/globeArt.js): one choice for each kind (Earth,
// Moon, spacecraft), shared by every diagram on the page, so the menu
// changes them all at once.
const ART_KEY = (kind) => `apollo-art-${kind}`
const artListeners = new Set()
const chosenArt = {}
function readArt(kind) {
  let id = null
  try {
    id = localStorage.getItem(ART_KEY(kind))
  } catch {
    /* none kept */
  }
  return ART[kind].some((a) => a.id === id) ? id : ART[kind][0].id
}
export function setGlobeArt(kind, id) {
  chosenArt[kind] = id
  try {
    localStorage.setItem(ART_KEY(kind), id)
  } catch {
    /* just for this visit */
  }
  artListeners.forEach((f) => f())
}
const subscribeArt = (f) => {
  artListeners.add(f)
  return () => artListeners.delete(f)
}
// The chosen art for 'earth', 'moon' or 'craft': its row from ART.
export function useGlobeArt(kind) {
  const id = useSyncExternalStore(subscribeArt, () => (chosenArt[kind] ??= readArt(kind)))
  return ART[kind].find((a) => a.id === id) || ART[kind][0]
}
