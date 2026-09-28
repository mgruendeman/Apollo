import { missionSources } from '../data/missionSources'

const GROUPS = [
  ['recordings', 'Recordings'],
  ['press', 'Press conferences'],
  ['transcripts', "NASA's transcripts"],
  ['documents', 'Reports and more'],
]

// Where to go further: NASA's recordings, press conferences, transcripts and
// reports for the mission (src/data/missionSources.js).
export default function MissionSources({ mission }) {
  const sources = missionSources[mission.id]
  if (!sources) return null
  return (
    <section className="mission-sources">
      <h3>Sources and more</h3>
      {GROUPS.filter(([key]) => sources[key]?.length).map(([key, label]) => (
        <div key={key} className="mission-sources-group">
          <h4>{label}</h4>
          <ul>
            {sources[key].map((s) => (
              <li key={s.url}>
                <a href={s.url} target="_blank" rel="noreferrer">
                  {s.title}
                </a>
                <span className="mission-sources-by">{s.by}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  )
}
