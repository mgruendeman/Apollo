import { useEffect, useMemo, useState } from 'react'
import PhotoLightbox from './PhotoLightbox'
import { likesAvailable, likeId, topLiked, useLikes } from '../lib/likes'
import missionPhotos from '../data/missionPhotos.json'
import { useFrames, frameToPhoto, nasaPhotoToPhoto, frameKey, KIND_LABELS } from '../lib/archiveFrames'

const PAGE = 60
const RANDOM_COUNT = 24

// A random selection that favours NASA's processed photos and the clearest
// scans (weighted sampling: each photo draws rand^(1/weight), top n win).
function randomPick(photos, n) {
  return photos
    .map((p) => ({ p, k: Math.random() ** (1 / (p.scan ? 1 + (p.quality ?? 3) : 12)) }))
    .sort((a, b) => b.k - a.k)
    .slice(0, n)
    .map((x) => x.p)
}
const OTHER_KINDS = { launch: 'Launch', recovery: 'Recovery', 'mission-control': 'Mission Control', crew: 'Crew' }

// Every photo we have for a mission: NASA's captioned selection, then each
// frame of the scanned Hasselblad and Nikon film, filterable by subject.
export default function PhotoGallery({ mission }) {
  const frames = useFrames(mission.id)
  const [kind, setKind] = useState('all')
  const [shown, setShown] = useState(PAGE)
  const [open, setOpen] = useState(null)
  const [mode, setMode] = useState('random')
  const [seed, setSeed] = useState(0)

  const all = useMemo(() => {
    const curated = (missionPhotos[mission.id] || []).map(nasaPhotoToPhoto)
    const seen = new Set(curated.map((p) => frameKey(p.key)))
    const scans = (frames || [])
      .filter((f) => !seen.has(frameKey(f[0])))
      .map((f) => frameToPhoto(f, mission.id))
    return [...curated, ...scans]
  }, [frames, mission.id])

  const counts = useMemo(() => {
    const c = {}
    for (const p of all) c[p.kind] = (c[p.kind] || 0) + 1
    return c
  }, [all])

  const filtered = useMemo(() => (kind === 'all' ? all : all.filter((p) => p.kind === kind)), [all, kind])
  // seed changes on each Shuffle, drawing a new batch.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const random = useMemo(() => randomPick(filtered, RANDOM_COUNT), [filtered, seed])

  // "Most liked": the mission's top photos by likes, fetched when chosen.
  const [top, setTop] = useState(null)
  useEffect(() => {
    if (mode !== 'liked') return undefined
    let live = true
    topLiked(mission.id).then((rows) => live && setTop(rows))
    return () => {
      live = false
    }
  }, [mode, mission.id])
  const liked = useMemo(() => {
    if (!top) return []
    const byId = new Map(filtered.map((p) => [likeId(p), p]))
    return top.map((r) => byId.get(r.photo)).filter(Boolean)
  }, [top, filtered])

  const photos = mode === 'random' ? random : mode === 'liked' ? liked : filtered
  const likes = useLikes(photos.slice(0, shown).map(likeId))
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
      <div className="photo-gallery-mode" role="group" aria-label="How to browse">
        <button type="button" className={mode === 'random' ? 'is-active' : ''} onClick={() => setMode('random')}>
          Random selection
        </button>
        <button type="button" className={mode === 'all' ? 'is-active' : ''} onClick={() => setMode('all')}>
          All, in order
        </button>
        {likesAvailable && (
          <button type="button" className={mode === 'liked' ? 'is-active' : ''} onClick={() => setMode('liked')}>
            ♥ Most liked
          </button>
        )}
        {mode === 'random' && (
          <button type="button" className="photo-gallery-shuffle" onClick={() => setSeed((n) => n + 1)}>
            ⟳ Shuffle
          </button>
        )}
      </div>
      <div className="photo-gallery-grid">
        {photos.slice(0, shown).map((p, i) => {
          const n = likes(likeId(p))?.count
          return (
            <button key={p.key} type="button" className={p.scan ? 'photo-thumb is-scan' : 'photo-thumb'} onClick={() => setOpen(i)} title={p.title}>
              <img src={p.thumb} alt={p.caption || p.title} loading="lazy" />
              {n > 0 && <span className="photo-thumb-likes">♥ {n}</span>}
            </button>
          )
        })}
      </div>
      {mode === 'liked' && top && liked.length === 0 && (
        <p className="photo-gallery-empty">No likes yet. Open a photo and tap ♡ on the ones you like best; they'll rise to the top here.</p>
      )}
      {mode === 'all' && shown < photos.length && (
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
