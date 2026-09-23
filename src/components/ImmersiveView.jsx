import { useEffect, useMemo, useRef, useState } from 'react'
import AudioPlayer from './AudioPlayer'
import SpeakerAvatar from './SpeakerAvatar'
import { PHASES } from '../data/phases'
import { formatGet } from '../lib/liveStatus'
import { effectiveOffsets, activeLineIndex } from '../lib/transcriptTiming'
import { useFrames, photosForMomentAll } from '../lib/archiveFrames'

const PHOTO_SECONDS = 12
// How long a manual scroll of the transcript pauses auto-scrolling.
const USER_SCROLL_HOLD_MS = 6000

// Just the spoken words: drop the journal editors' bracketed notes, which
// can run to paragraphs and would crowd the photo off the screen.
function spokenText(text) {
  return text.replace(/\[[^\]]*\]?/g, '').replace(/\s+/g, ' ').trim()
}
const MAX_PHOTOS = 24

function PhotoStage({ photos }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (photos.length < 2) return
    const t = setInterval(() => setIndex((i) => (i + 1) % photos.length), PHOTO_SECONDS * 1000)
    return () => clearInterval(t)
  }, [photos])

  if (photos.length === 0) {
    return (
      <div className="immersive-photo is-empty">
        <p>No NASA photos matched to this part of the mission yet.</p>
      </div>
    )
  }
  const photo = photos[index % photos.length]
  return (
    <figure className="immersive-photo">
      <img key={photo.src} src={photo.src} alt={photo.caption} />
      <figcaption>
        <a href={photo.sourceUrl} target="_blank" rel="noreferrer">
          {photo.credit} ↗
        </a>
        {photos.length > 1 && (
          <span className="immersive-photo-count">
            {(index % photos.length) + 1} / {photos.length}
          </span>
        )}
      </figcaption>
    </figure>
  )
}

// A separate, distraction-free mode: the photo for the current moment fills
// the screen, with the conversation running underneath it.
export default function ImmersiveView({
  mission,
  clips,
  index,
  lines,
  currentTime,
  phase,
  highlightPhoto,
  onClose,
  onLineSeek,
  onPrevious,
  onNext,
}) {
  const rootRef = useRef(null)
  const clip = clips[index]

  // Photos depend only on the day, phase and any highlight photo, so the
  // slideshow keeps going across clip changes within the same stretch.
  const dayMs = 24 * 3600 * 1000
  const utcDay = Math.floor((Date.parse(mission.launchUtc) + clip.getSeconds * 1000) / dayMs)
  const frames = useFrames(mission.id)
  const poolKey = `${phase}-${utcDay}-${highlightPhoto?.src || ''}-${frames ? 'all' : 'nasa'}`

  // NASA's captioned photos first, then the clearest film-roll scans.
  const photos = useMemo(() => {
    const utcMs = utcDay * dayMs + dayMs / 2
    const matched = photosForMomentAll(mission.id, frames || [], utcMs, phase, MAX_PHOTOS).map((p) => ({
      src: p.full,
      caption: p.caption,
      credit: p.credit,
      sourceUrl: p.sourceUrl,
    }))
    if (!highlightPhoto) return matched
    return [{ ...highlightPhoto, src: `${import.meta.env.BASE_URL}${highlightPhoto.src}` }, ...matched]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [poolKey])

  const offsets = useMemo(() => effectiveOffsets(lines), [lines])
  const active = activeLineIndex(offsets, currentTime)
  const shown = useMemo(
    () => lines.map((line, i) => ({ line, i, text: spokenText(line.text) })).filter((l) => l.text),
    [lines],
  )

  // The whole clip's transcript scrolls; it follows the line being spoken
  // unless the listener has just scrolled it themselves.
  const listRef = useRef(null)
  const activeRef = useRef(null)
  const userScrolledAt = useRef(0)
  const shownLines = useRef(null)
  useEffect(() => {
    const list = listRef.current
    const line = activeRef.current
    if (!list || !line) return
    const newClip = shownLines.current !== lines
    shownLines.current = lines
    if (!newClip && Date.now() - userScrolledAt.current < USER_SCROLL_HOLD_MS) return
    list.scrollTo({
      top: line.offsetTop - list.clientHeight / 2 + line.clientHeight / 2,
      behavior: newClip ? 'auto' : 'smooth',
    })
  }, [active, lines])

  function markUserScroll() {
    userScrolledAt.current = Date.now()
  }

  useEffect(() => {
    const el = rootRef.current
    el?.requestFullscreen?.().catch(() => {})
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    function onKey(e) {
      if (e.key === 'Escape' && !document.fullscreenElement) onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = previous
      document.removeEventListener('keydown', onKey)
      if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {})
    }
  }, [onClose])

  return (
    <div className="immersive" ref={rootRef} role="dialog" aria-modal="true" aria-label={`${mission.name} full-screen view`}>
      <header className="immersive-top">
        <div>
          <span className="immersive-mission">{mission.name}</span>
          <span className="immersive-get">GET {formatGet(clip.getSeconds + currentTime)}</span>
          {PHASES[phase] && <span className="immersive-phase">{PHASES[phase].label}</span>}
        </div>
        <button type="button" className="immersive-close" onClick={onClose} aria-label="Exit full-screen view">
          ×
        </button>
      </header>

      <PhotoStage key={poolKey} photos={photos} />

      <div
        className="immersive-transcript"
        ref={listRef}
        onWheel={markUserScroll}
        onTouchMove={markUserScroll}
        onKeyDown={markUserScroll}
      >
        {shown.length === 0 && <p className="immersive-empty">No transcript for this clip.</p>}
        {shown.map(({ line, i, text }) => (
          <button
            type="button"
            key={`${line.get}-${i}`}
            ref={i === active ? activeRef : null}
            className={i === active ? 'immersive-line is-active' : i < active ? 'immersive-line is-past' : 'immersive-line'}
            onClick={() => onLineSeek(offsets[i])}
          >
            <SpeakerAvatar name={line.speaker} />
            <span>
              <span className="immersive-speaker">{line.speaker}</span>
              <span className="immersive-text">{text}</span>
            </span>
          </button>
        ))}
      </div>

      <div className="immersive-controls">
        <button type="button" className="immersive-skip" onClick={onPrevious} disabled={!onPrevious} aria-label="Previous clip">
          ⏮
        </button>
        <AudioPlayer mission={mission} clips={clips} index={index} />
        <button type="button" className="immersive-skip" onClick={onNext} disabled={!onNext} aria-label="Next clip">
          ⏭
        </button>
      </div>
    </div>
  )
}
