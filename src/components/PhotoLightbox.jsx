import { useEffect, useState } from 'react'
import { track } from '../lib/track'
import LikeButton from './LikeButton'
import ReportDialog from './ReportDialog'
import { KIND_LABELS } from '../lib/archiveFrames'

// Large view of one photo from a list, with arrow-key paging. `where` says
// where the photo was being shown ("with GET 102:45:40, Descent to the
// Surface"), for a report that it's in the wrong place.
export default function PhotoLightbox({ photos, index, onIndex, onClose, missionName, where }) {
  const photo = photos[index]
  const [reporting, setReporting] = useState(false)

  useEffect(() => {
    function onKey(e) {
      if (reporting) return   // (the report form has the keys)
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft' && index > 0) onIndex(index - 1)
      else if (e.key === 'ArrowRight' && index < photos.length - 1) onIndex(index + 1)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [index, photos.length, onIndex, onClose, reporting])

  useEffect(() => {
    if (photo?.title) track('photo', (photo.title.match(/^AS(\d+)/i) || [])[1] || '', photo.title)
  }, [photo?.title])

  if (!photo) return null
  const context = [
    `Photo ${photo.title}${photo.kind ? `, filed as ${KIND_LABELS[photo.kind] || photo.kind}` : ''}${photo.date ? `, ${photo.date}` : ''}`,
    where && `Shown ${where}`,
    `Image: ${photo.full}`,
  ]
    .filter(Boolean)
    .join('\n')
  return (
    <>
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={photo.title} onClick={onClose}>
      <figure className="lightbox-figure" onClick={(e) => e.stopPropagation()}>
        <div className="lightbox-image" style={{ backgroundImage: `url("${photo.thumb}")` }}>
          <img key={photo.full} src={photo.full} alt={photo.caption || photo.title} />
        </div>
        <figcaption>
          <span className="lightbox-caption">{photo.caption}</span>
          <span className="lightbox-meta">
            {photo.title}
            {photo.date && ` · ${photo.date}`} · {index + 1} of {photos.length}
          </span>
          <span className="lightbox-links">
            <LikeButton photo={photo} />
            <a href={photo.full} target="_blank" rel="noreferrer">
              Open image ↗
            </a>
            <a href={photo.sourceUrl} target="_blank" rel="noreferrer">
              {photo.credit} ↗
            </a>
            <button type="button" className="lightbox-report" onClick={() => setReporting(true)}>
              Wrong place? Report a problem
            </button>
          </span>
        </figcaption>
        <button type="button" className="lightbox-close" onClick={onClose} aria-label="Close photo">
          ×
        </button>
        {index > 0 && (
          <button type="button" className="lightbox-nav is-prev" onClick={() => onIndex(index - 1)} aria-label="Previous photo">
            ‹
          </button>
        )}
        {index < photos.length - 1 && (
          <button type="button" className="lightbox-nav is-next" onClick={() => onIndex(index + 1)} aria-label="Next photo">
            ›
          </button>
        )}
      </figure>
    </div>
    {reporting && (
      <ReportDialog
        title={`${missionName || 'Photo'}: photo ${photo.title}`}
        context={context}
        placeholder="e.g. this was taken on the second moonwalk, not the first; it's upside down; it belongs with the landing"
        onClose={() => setReporting(false)}
      />
    )}
    </>
  )
}
