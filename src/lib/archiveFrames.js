import { useEffect, useState } from 'react'
import { KINDS_FOR_PHASE, photosForMoment, nasaImageUrl } from './momentPhotos'
import missionPhotos from '../data/missionPhotos.json'
import { MEDIA_URL } from '../config'

// Every Hasselblad and Nikon frame from the NASA JSC / Arizona State
// University "March to the Moon" scans, indexed per mission by
// scripts/fetch_archive_frames.py. Rows are
// [frameId, format, kind, date, description, quality 0-9]; the index is
// fetched on demand because the bigger missions run to hundreds of KB.
// Loaded rows gain [.., cleaned 0/1, mission time or null]: the time a
// frame was taken, where pipeline/photo_times.py could place it
// (<mission>.times.json, from the film order and anchors).

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

// <mission>.cleaned.json (from pipeline/upload_photos.py) lists the frames
// that have a cleaned-up photo on our media host, and the frames reviewers
// rejected (blank, fogged, blurred), which aren't shown at all.
const getJson = (path, empty) =>
  fetch(`${import.meta.env.BASE_URL}${path}`).then((r) => (r.ok ? r.json() : empty)).catch(() => empty)

export function loadFrames(missionId) {
  if (!cache.has(missionId)) {
    const p = Promise.all([
      getJson(`photo-index/${missionId}.json`, { frames: [] }),
      getJson(`photo-index/${missionId}.cleaned.json`, { cleaned: [], rejected: [] }),
      getJson(`photo-index/${missionId}.times.json`, { frames: {}, kinds: {} }),
    ])
      .then(([index, media, times]) => {
        const rejected = new Set(media.rejected)
        const cleaned = new Set(MEDIA_URL ? media.cleaned : [])
        const at = times.frames || {}, refiled = times.kinds || {}
        return index.frames
          .filter((f) => !rejected.has(f[0]))
          .map(([id, fmt, kind, ...rest]) => [id, fmt, refiled[id] || kind, ...rest.slice(0, 3), cleaned.has(id) ? 1 : 0, at[id] ?? null])
      })
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
export function frameToPhoto([id, format, kind, date, desc, quality, cleaned], missionId) {
  const ours = cleaned && `${MEDIA_URL}/photos/${id.slice(2, 4)}/${id}`
  return {
    key: id,
    thumb: ours ? `${ours}.thumb.jpg` : frameUrl(id, format, 'thumb'),
    full: ours ? `${ours}.jpg` : frameUrl(id, format, 'small'),
    kind,
    caption: desc || KIND_LABELS[kind] || '',
    title: id,
    credit: ours ? `NASA JSC / ASU film scan, cleaned up (${id})` : `Film scan: NASA JSC / ASU (${id})`,
    // Cleaned photos are already cropped to the picture; raw scans still show the film edge.
    scan: !ours,
    quality,
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

// How close to a moment a timed photo must be to show with it.
const NEAR_SECONDS = 20 * 60

// Photos taken at this moment (`get`, the mission time) first, nearest first,
// where the film order has placed them; then curated NASA Image Library
// photos (they have real captions), then archive frames, for the day and
// phase. A photo whose time is known and isn't near this moment waits for
// its own.
export function photosForMomentAll(missionId, frames, utcMs, phase, limit = 24, get = null) {
  const timeOf = new Map(frames.filter((f) => f[7] != null).map((f) => [frameKey(f[0]), f[7]]))
  const elsewhere = (key) => get != null && timeOf.has(key) && Math.abs(timeOf.get(key) - get) > NEAR_SECONDS
  const nasa = new Map((missionPhotos[missionId] || []).map((p) => [frameKey(p.id), p]))
  const timed = get == null ? [] : frames
    .filter((f) => f[7] != null && Math.abs(f[7] - get) <= NEAR_SECONDS)
    .sort((a, b) => Math.abs(a[7] - get) - Math.abs(b[7] - get))
    .map((f) => (nasa.has(frameKey(f[0])) ? nasaPhotoToPhoto(nasa.get(frameKey(f[0]))) : frameToPhoto(f, missionId)))
  const seen = new Set(timed.map((p) => frameKey(p.key)))
  const curated = photosForMoment(missionId, utcMs, phase)
    .filter((p) => !seen.has(frameKey(p.id)) && !elsewhere(frameKey(p.id)))
    .map(nasaPhotoToPhoto)
  curated.forEach((p) => seen.add(frameKey(p.key)))
  const extra = framesForMoment(frames, utcMs, phase, limit)
    .filter((f) => !seen.has(frameKey(f[0])) && !elsewhere(frameKey(f[0])))
    .map((f) => frameToPhoto(f, missionId))
  return [...timed, ...curated, ...extra].slice(0, limit)
}
