import { useEffect } from 'react'
import LikeButton from './LikeButton'

// Large view of one photo from a list, with arrow-key paging.
export default function PhotoLightbox({ photos, index, onIndex, onClose }) {
  const photo = photos[index]

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft' && index > 0) onIndex(index - 1)
      else if (e.key === 'ArrowRight' && index < photos.length - 1) onIndex(index + 1)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [index, photos.length, onIndex, onClose])

  if (!photo) return null
  return (
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
  )
}
