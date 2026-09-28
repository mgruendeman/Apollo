import { Link } from 'react-router-dom'
import { stageOf, useProgress } from '../lib/progress'

const n = (x) => x.toLocaleString('en-US')
const day = (iso) => new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })

// "Under construction" on a mission's page: what's done, what's under way
// and what's still to come, with the numbers where there are some.
export default function MissionProgress({ mission }) {
  const all = useProgress()
  const stage = stageOf(mission)
  const p = all?.[mission.id]
  const missionHours = Math.round(mission.durationSeconds / 3600)

  let steps
  if (stage === 'tapes') {
    steps = [
      {
        state: 'done',
        title: "NASA's tapes placed on the mission clock",
        text: p ? `${Math.round(p.recordedHours)} of the mission's ${missionHours} hours have a recording.` : null,
      },
      {
        state: 'done',
        title: "NASA's transcript timed to the tapes",
        text: p ? `${n(p.lines)} lines, plus ${n(p.announcerLines)} from the announcer, transcribed from the tapes.` : null,
      },
      {
        state: 'doing',
        title: 'Checking the transcript against the tapes',
        text: p
          ? `${n(p.corrected)} lines corrected so far. ${n(p.flagged)} more are flagged for a listen: a damaged word, the tape hearing something else, or a speaker to confirm.`
          : null,
      },
    ]
  } else if (stage === 'clips') {
    steps = [
      { state: 'done', title: 'Clips of the key moments', text: 'From the Apollo Flight Journal and Apollo Lunar Surface Journal, for now.' },
      {
        state: 'todo',
        title: "The whole mission from NASA's tapes",
        text: "Still to come: NASA's tapes placed on the mission clock, with NASA's transcript timed to them and checked.",
      },
    ]
  } else {
    steps = [
      { state: 'done', title: "NASA's recordings, listed", text: 'As archive.org has them, to play one at a time.' },
      { state: 'todo', title: 'On the mission clock, with the transcript', text: "Still to come: the recordings placed on the mission clock, with NASA's transcript timed to them." },
    ]
  }

  return (
    <section className="mission-progress" aria-label={`Where ${mission.name} is at`}>
      <h2>
        <span aria-hidden="true">🚧</span> Work in progress
      </h2>
      <ol className="progress-steps">
        {steps.map((s) => (
          <li key={s.title} className={`is-${s.state}`}>
            <span className="progress-mark" aria-hidden="true">
              {s.state === 'done' ? '✓' : s.state === 'doing' ? '◐' : '○'}
            </span>
            <span>
              <strong>{s.title}</strong>
              <span className="progress-state">{s.state === 'done' ? ' · done' : s.state === 'doing' ? ' · under way' : ' · to do'}</span>
              {s.text && <span className="progress-text">{s.text}</span>}
            </span>
          </li>
        ))}
      </ol>
      {stage === 'tapes' && (
        <p className="progress-note">
          {p && <>Updated {day(p.updated)}. </>}Spot a mistake? Press and hold the line to tell me (<Link to="/guide">how</Link>).
        </p>
      )}
    </section>
  )
}
