import { useMemo, useState } from 'react'
import PhotoLightbox from './PhotoLightbox'
import { useFrames, photosForMomentAll } from '../lib/archiveFrames'

const DAY_MS = 24 * 3600 * 1000
const MAX = 16

// A row of photos from the same day and phase of the flight as the clip
// that's playing: NASA's captioned photos first, then frames from the
// complete film-roll scans.
export default function MomentPhotos({ mission, clip, phase }) {
  const frames = useFrames(mission.id)
  const [open, setOpen] = useState(null)
  const utcDay = Math.floor((Date.parse(mission.launchUtc) + clip.getSeconds * 1000) / DAY_MS)

  const photos = useMemo(
    () => (frames ? photosForMomentAll(mission.id, frames, utcDay * DAY_MS + DAY_MS / 2, phase, MAX) : []),
    [frames, mission.id, utcDay, phase],
  )

  if (photos.length === 0) return null
  return (
    <section className="moment-photos" aria-label="Photos from this part of the flight">
      <h3>Photos from this part of the flight</h3>
      <div className="moment-photos-row">
        {photos.map((p, i) => (
          <button key={p.key} type="button" className={p.scan ? 'photo-thumb is-scan' : 'photo-thumb'} onClick={() => setOpen(i)} title={p.caption}>
            <img src={p.thumb} alt={p.caption || p.title} loading="lazy" />
          </button>
        ))}
      </div>
      {open !== null && <PhotoLightbox photos={photos} index={open} onIndex={setOpen} onClose={() => setOpen(null)} />}
    </section>
  )
}
