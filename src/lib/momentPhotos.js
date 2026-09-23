import missionPhotos from '../data/missionPhotos.json'

// Which kinds of NASA photo fit each phase of the flight.
export const KINDS_FOR_PHASE = {
  launch: ['launch'],
  'earth-orbit': ['earth', 'launch', 'interior'],
  'transit-to-moon': ['earth', 'interior', 'other'],
  'lunar-orbit': ['lunar-orbit', 'interior'],
  landing: ['lunar-orbit', 'surface'],
  surface: ['surface'],
  ascent: ['lunar-orbit', 'surface'],
  'transit-to-earth': ['earth', 'lunar-orbit', 'interior', 'other'],
  splashdown: ['recovery'],
}

const DAY_MS = 24 * 3600 * 1000

export function nasaImageUrl(id, size = 'large') {
  return `https://images-assets.nasa.gov/image/${id}/${id}~${size}.jpg`
}

// NASA photos that fit a moment: the right kind for the flight phase, taken
// on that day where NASA's caption dates the frame (captions use US local
// dates, so a day either side counts), then undated frames of the right
// kind. Mission Control photos from the same day are included too.
export function photosForMoment(missionId, utcMs, phase) {
  const pool = missionPhotos[missionId] || []
  const kinds = KINDS_FOR_PHASE[phase] || []
  const scored = []
  for (const p of pool) {
    const nearDay = p.date && Math.abs(Date.parse(`${p.date}T12:00:00Z`) - utcMs) <= 1.5 * DAY_MS
    let score = 0
    if (kinds.includes(p.kind)) score = nearDay ? 3 : p.date ? 0 : 2
    else if (p.kind === 'mission-control' && nearDay) score = 1
    if (score > 0) scored.push({ p, score })
  }
  scored.sort((a, b) => b.score - a.score)
  return scored.map((s) => s.p)
}
