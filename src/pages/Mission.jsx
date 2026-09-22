import { useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import AudioPlayer from '../components/AudioPlayer'
import { findMission } from '../data/missions'

export default function Mission() {
  const { id } = useParams()
  const mission = findMission(id)
  const [activeIndex, setActiveIndex] = useState(0)

  if (!mission || mission.status !== 'available') {
    return <Navigate to="/" replace />
  }

  const moment = mission.moments[activeIndex]

  return (
    <div className="page">
      <Link to="/" className="back-link">
        ← All missions
      </Link>

      <header className="mission-header">
        <p className="eyebrow">Apollo {mission.number}</p>
        <h1>{mission.name}</h1>
        <p className="mission-header-dates">{mission.dates}</p>
        <p className="mission-header-crew">{mission.crew.join(' · ')}</p>
        <p className="lede">{mission.summary}</p>
      </header>

      <section className="player-section">
        <p className="get-clock">GET {moment.get}</p>
        <h2>{moment.title}</h2>
        <AudioPlayer key={moment.id} moment={moment} />
        <p className="moment-description">{moment.description}</p>
        <a
          className="source-link"
          href={moment.sourceUrl}
          target="_blank"
          rel="noreferrer"
        >
          Source & full transcript: {moment.sourceLabel} ↗
        </a>
      </section>

      <section className="moments-list">
        <h3>Key moments</h3>
        <ol>
          {mission.moments.map((m, i) => (
            <li key={m.id}>
              <button
                type="button"
                className={i === activeIndex ? 'moment-item is-active' : 'moment-item'}
                onClick={() => setActiveIndex(i)}
              >
                <span className="moment-get">{m.get}</span>
                <span className="moment-title">{m.title}</span>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
