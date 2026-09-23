import { useEffect, useState } from 'react'
import { KINDS_FOR_PHASE, photosForMoment, nasaImageUrl } from './momentPhotos'

// Every Hasselblad and Nikon frame from the NASA JSC / Arizona State
// University "March to the Moon" scans, indexed per mission by
// scripts/fetch_archive_frames.py. Rows are
// [frameId, format, kind, date, description, quality 0-9]; the index is
// fetched on demand because the bigger missions run to hundreds of KB.

const ARCHIVE = 'https://tothemoon.im-ldi.com'
const DAY_MS = 24 * 3600 * 1000
const cache = new Map()

export const KIND_LABELS = {
  earth: 'Earth',
  'lunar-orbit': 'Lunar orbit',
  surface: 'Lunar surface',
  interior: 'Inside the spacecraft',
  other: 'Other',
}

export function loadFrames(missionId) {
  if (!cache.has(missionId)) {
    const p = fetch(`${import.meta.env.BASE_URL}photo-index/${missionId}.json`)
      .then((r) => (r.ok ? r.json() : { frames: [] }))
      .then((d) => d.frames)
      .catch(() => {
        cache.delete(missionId)
        return []
      })
    cache.set(missionId, p)
  }
  return cache.get(missionId)
}

// The mission's archive frames, or null while they load.
export function useFrames(missionId) {
  const [loaded, setLoaded] = useState({ id: null, frames: null })
  useEffect(() => {
    let live = true
    loadFrames(missionId).then((frames) => live && setLoaded({ id: missionId, frames }))
    return () => {
      live = false
    }
  }, [missionId])
  return loaded.id === missionId ? loaded.frames : null
}

// "KSC-as11-40-5875", "AS11-40-5875" and "as11-040-05875" are one frame.
export function frameKey(id) {
  const m = /^(?:KSC-)?AS(\d\d)-0*(\d+[A-D]?)-0*(\d+)/i.exec(id)
  return m ? `${m[1]}-${m[2].toUpperCase()}-${m[3]}` : id.toUpperCase()
}

function frameUrl(id, format, size) {
  const roll = id.slice(0, 4).toUpperCase()
  if (format === 'b') return `${ARCHIVE}/data_a/${roll}/png/${id}_${size === 'thumb' ? 'THM' : 'SML'}.png`
  return `${ARCHIVE}/data_a70/${roll}/extra/${id}.${size}.png`
}

// One shape for both photo sources, so the strip, gallery, lightbox and
// full-screen view don't care where a picture came from.
export function frameToPhoto([id, format, kind, date, desc], missionId) {
  return {
    key: id,
    thumb: frameUrl(id, format, 'thumb'),
    full: frameUrl(id, format, 'small'),
    kind,
    caption: desc || KIND_LABELS[kind] || '',
    title: id,
    credit: `Film scan: NASA JSC / ASU (${id})`,
    scan: true,
    sourceUrl: `${ARCHIVE}/gallery/Apollo/${Number(missionId)}`,
    date,
  }
}

export function nasaPhotoToPhoto(p) {
  return {
    key: p.id,
    thumb: nasaImageUrl(p.id, 'small'),
    full: nasaImageUrl(p.id),
    kind: p.kind,
    caption: p.caption,
    title: p.id.toUpperCase(),
    credit: `NASA (${p.id.toUpperCase()})`,
    sourceUrl: `https://images.nasa.gov/details/${p.id}`,
    date: p.date,
  }
}

// Archive frames that fit a moment: the right kind for the phase, taken
// that day (or the day either side) where the frame has a date, then the
// clearest undated frames of that kind.
export function framesForMoment(frames, utcMs, phase, limit = 24) {
  const kinds = KINDS_FOR_PHASE[phase] || []
  const onDay = []
  const undated = []
  for (const f of frames) {
    if (!kinds.includes(f[2])) continue
    if (f[3]) {
      if (Math.abs(Date.parse(`${f[3]}T12:00:00Z`) - utcMs) <= 1.5 * DAY_MS) onDay.push(f)
    } else {
      undated.push(f)
    }
  }
  const byQuality = (a, b) => b[5] - a[5]
  onDay.sort(byQuality)
  undated.sort(byQuality)
  return [...onDay, ...undated].slice(0, limit)
}

// Curated NASA Image Library photos first (they have real captions), then
// archive frames.
export function photosForMomentAll(missionId, frames, utcMs, phase, limit = 24) {
  const curated = photosForMoment(missionId, utcMs, phase).map(nasaPhotoToPhoto)
  const seen = new Set(curated.map((p) => frameKey(p.key)))
  const extra = framesForMoment(frames, utcMs, phase, limit)
    .filter((f) => !seen.has(frameKey(f[0])))
    .map((f) => frameToPhoto(f, missionId))
  return [...curated, ...extra].slice(0, limit)
}
