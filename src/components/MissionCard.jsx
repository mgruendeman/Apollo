import { Link } from 'react-router-dom'

export default function MissionCard({ mission }) {
  const available = mission.status === 'available' || mission.status === 'archive'

  const card = (
    <div className={`mission-card ${available ? 'is-available' : 'is-soon'}`}>
      <h3>{mission.name}</h3>
      <p className="mission-card-dates">{mission.dates}</p>
      <p className="mission-card-summary">{mission.summary}</p>
      <div className="mission-card-footer">
        {mission.status === 'archive' ? (
          <span className="badge badge-available">Full NASA tapes</span>
        ) : available ? (
          <span className="badge badge-available">
            {mission.clipCount.toLocaleString()} audio clips
          </span>
        ) : (
          <span className="badge badge-soon">Coming soon</span>
        )}
      </div>
    </div>
  )

  return available ? (
    <Link to={`/mission/${mission.id}`} className="mission-card-link">
      {card}
    </Link>
  ) : (
    <div className="mission-card-link is-disabled">{card}</div>
  )
}
