export default function MissionPhoto({ photo }) {
  if (!photo) return null
  return (
    <figure className="mission-photo">
      <a href={photo.sourceUrl} target="_blank" rel="noreferrer">
        <img src={`${import.meta.env.BASE_URL}${photo.src}`} alt={photo.caption} loading="lazy" />
      </a>
      <figcaption>
        <span>{photo.caption}</span>
        <a className="mission-photo-credit" href={photo.sourceUrl} target="_blank" rel="noreferrer">
          {photo.credit} ↗
        </a>
      </figcaption>
    </figure>
  )
}
