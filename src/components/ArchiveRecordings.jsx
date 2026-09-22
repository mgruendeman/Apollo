import { usePlayer } from '../audio/PlayerContext'
import AudioPlayer from './AudioPlayer'

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.round((seconds % 3600) / 60)
  return h ? `${h} h ${m} min` : `${m} min`
}

export default function ArchiveRecordings({ mission, archive }) {
  const player = usePlayer()
  // A separate session id keeps these whole recordings apart from the
  // mission's synced clip list in the shared player.
  const session = { ...mission, id: `${mission.id}-archive`, routeId: mission.id }
  const clips = archive.recordings.map((r) => ({
    id: r.id,
    get: null,
    getSeconds: 0,
    audioUrl: r.url,
    sourceUrl: archive.collection,
    sourceLabel: r.title,
  }))

  return (
    <section className="archive-recordings">
      <h3>Full NASA recordings</h3>
      <p className="archive-intro">
        Whole, uncut tapes from NASA&apos;s Johnson Space Center Audio Control Room. They aren&apos;t
        synced to the mission clock or transcribed here yet.
      </p>
      {archive.recordings.length > 0 && (
        <ul>
          {archive.recordings.map((r, i) => {
            const active = player.session?.mission.id === session.id && player.session.index === i
            return (
              <li key={r.id} className={active ? 'archive-item is-active' : 'archive-item'}>
                <div className="archive-item-text">
                  <span className="archive-item-title">{r.title}</span>
                  <span className="archive-item-meta">{formatDuration(r.durationSeconds)}</span>
                  <span className="archive-item-desc">{r.description}</span>
                </div>
                <AudioPlayer mission={session} clips={clips} index={i} />
              </li>
            )
          })}
        </ul>
      )}
      <a className="source-link" href={archive.collection} target="_blank" rel="noreferrer">
        Browse all ~{archive.hoursInCollection} hours of raw {mission.name} tapes on the Internet
        Archive ↗
      </a>
    </section>
  )
}
