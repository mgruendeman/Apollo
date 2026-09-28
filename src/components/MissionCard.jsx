import { Link } from 'react-router-dom'
import { patchFor } from '../data/patches'
import { stageOf, useProgress } from '../lib/progress'

// Where the mission is at, in a line: the transcript check's numbers for a
// tape mission, else what it plays for now.
function statusLine(mission, progress) {
  const stage = stageOf(mission)
  if (stage === 'tapes') {
    const p = progress?.[mission.id]
    return p
      ? `Checking the transcript: ${p.corrected.toLocaleString('en-US')} lines corrected, ${p.flagged.toLocaleString('en-US')} to listen to`
      : 'Checking the transcript'
  }
  if (stage === 'clips') return "Clips for now · NASA's tapes to come"
  return 'Recordings listed · not yet on the mission clock'
}

export default function MissionCard({ mission }) {
  const progress = useProgress()
  const available = mission.status === 'available' || mission.status === 'archive'
  const patch = patchFor(mission.id)

  const card = (
    <div className={`mission-card ${available ? 'is-available' : 'is-soon'}`}>
      <div className="mission-card-head">
        {patch && <img className="mission-card-patch" src={patch} alt={`${mission.name} mission emblem`} loading="lazy" />}
        <div>
          <h3>{mission.name}</h3>
          <p className="mission-card-dates">{mission.dates}</p>
        </div>
      </div>
      <p className="mission-card-summary">{mission.summary}</p>
      <div className="mission-card-footer">
        {mission.timeline ? (
          <span className="badge badge-available">Whole mission, NASA&apos;s tapes</span>
        ) : mission.status === 'archive' ? (
          <span className="badge badge-available">Full NASA tapes</span>
        ) : available ? (
          <span className="badge badge-available">
            {mission.clipCount.toLocaleString()} audio clips
          </span>
        ) : (
          <span className="badge badge-soon">Coming soon</span>
        )}
        {available && <p className="mission-card-status">🚧 {statusLine(mission, progress)}</p>}
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
