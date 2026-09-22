import { Link } from 'react-router-dom'

export default function MissionCard({ mission }) {
  const available = mission.status === 'available'

  const card = (
    <div className={`mission-card ${available ? 'is-available' : 'is-soon'}`}>
      <div className="mission-card-number">{mission.number}</div>
      <h3>{mission.name}</h3>
      <p className="mission-card-dates">{mission.dates}</p>
      <p className="mission-card-summary">{mission.summary}</p>
      <div className="mission-card-footer">
        {available ? (
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
