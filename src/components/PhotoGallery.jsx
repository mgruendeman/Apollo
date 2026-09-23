import { useMemo, useState } from 'react'
import PhotoLightbox from './PhotoLightbox'
import missionPhotos from '../data/missionPhotos.json'
import { useFrames, frameToPhoto, nasaPhotoToPhoto, KIND_LABELS } from '../lib/archiveFrames'

const PAGE = 60
const OTHER_KINDS = { launch: 'Launch', recovery: 'Recovery', 'mission-control': 'Mission Control', crew: 'Crew' }

// Every photo we have for a mission: NASA's captioned selection, then each
// frame of the scanned Hasselblad and Nikon film, filterable by subject.
export default function PhotoGallery({ mission }) {
  const frames = useFrames(mission.id)
  const [kind, setKind] = useState('all')
  const [shown, setShown] = useState(PAGE)
  const [open, setOpen] = useState(null)

  const all = useMemo(() => {
    const curated = (missionPhotos[mission.id] || []).map(nasaPhotoToPhoto)
    const seen = new Set(curated.map((p) => p.key.toUpperCase()))
    const scans = (frames || [])
      .filter((f) => !seen.has(f[0].toUpperCase()))
      .map((f) => frameToPhoto(f, mission.id))
    return [...curated, ...scans]
  }, [frames, mission.id])

  const counts = useMemo(() => {
    const c = {}
    for (const p of all) c[p.kind] = (c[p.kind] || 0) + 1
    return c
  }, [all])

  const photos = kind === 'all' ? all : all.filter((p) => p.kind === kind)
  if (all.length === 0) return null

  function pick(k) {
    setKind(k)
    setShown(PAGE)
  }

  const label = (k) => KIND_LABELS[k] || OTHER_KINDS[k] || k
  return (
    <section className="photo-gallery">
      <h2>Photos</h2>
      <p className="photo-gallery-intro">
        {all.length.toLocaleString()} photos: NASA's captioned selection, then every frame of the mission's
        Hasselblad {mission.id >= '16' ? 'and Nikon ' : ''}film as scanned by NASA's Johnson Space Center and
        Arizona State University.{frames === null && ' Loading the film scans…'}
      </p>
      <div className="photo-gallery-filters" role="group" aria-label="Filter photos">
        <button type="button" className={kind === 'all' ? 'is-active' : ''} onClick={() => pick('all')}>
          All <span>{all.length}</span>
        </button>
        {Object.entries(counts)
          .sort((a, b) => b[1] - a[1])
          .map(([k, n]) => (
            <button key={k} type="button" className={kind === k ? 'is-active' : ''} onClick={() => pick(k)}>
              {label(k)} <span>{n}</span>
            </button>
          ))}
      </div>
      <div className="photo-gallery-grid">
        {photos.slice(0, shown).map((p, i) => (
          <button key={p.key} type="button" className="photo-thumb" onClick={() => setOpen(i)} title={p.title}>
            <img src={p.thumb} alt={p.caption || p.title} loading="lazy" />
          </button>
        ))}
      </div>
      {shown < photos.length && (
        <button type="button" className="photo-gallery-more" onClick={() => setShown((s) => s + PAGE * 2)}>
          Show more ({(photos.length - shown).toLocaleString()} left)
        </button>
      )}
      {open !== null && (
        <PhotoLightbox photos={photos} index={open} onIndex={setOpen} onClose={() => setOpen(null)} />
      )}
    </section>
  )
}
