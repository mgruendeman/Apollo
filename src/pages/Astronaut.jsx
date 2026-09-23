import { Link, useParams } from 'react-router-dom'
import { astronauts } from '../data/astronauts'
import facts from '../data/astronautFacts.json'
import { findMission } from '../data/missions'
import { speakerAvatar } from '../data/speakers'
import ReportIssueButton from '../components/ReportIssueButton'

// Which programme a flight belongs to, for grouping.
const PROGRAMS = [
  ['Mercury', /^Mercury/],
  ['Gemini', /^Gemini/],
  ['Apollo', /^Apollo \d/],
  ['Skylab', /^Skylab/],
  ['Apollo–Soyuz', /^Apollo–Soyuz/],
  ['Space Shuttle', /^STS/],
]

function groupFlights(missions) {
  return PROGRAMS.map(([name, re]) => [name, missions.filter((m) => re.test(m))]).filter(([, list]) => list.length)
}

export default function Astronaut() {
  const { id } = useParams()
  const person = astronauts[id]

  if (!person) {
    return (
      <div className="page">
        <Link to="/astronauts" className="back-link">
          ← Astronauts
        </Link>
        <h1>Not found</h1>
      </div>
    )
  }

  const photo = speakerAvatar(id)
  const fact = facts[id]

  return (
    <div className="page">
      <Link to="/astronauts" className="back-link">
        ← Astronauts
      </Link>
      <header className="astronaut-header">
        {photo && <img src={photo} alt={person.name} className="astronaut-portrait" />}
        <div>
          <p className="eyebrow">Astronaut</p>
          <h1>{person.name}</h1>
          <p className="mission-header-dates">{person.years}</p>
        </div>
      </header>

      {fact && (
        <dl className="astronaut-facts">
          {fact.born && (
            <div>
              <dt>Born</dt>
              <dd>{fact.born}</dd>
            </div>
          )}
          {fact.service.length > 0 && (
            <div>
              <dt>Service</dt>
              <dd>{fact.service.join('; then ')}</dd>
            </div>
          )}
          {fact.missions.length > 0 && (
            <div>
              <dt>Spaceflights</dt>
              <dd>
                {groupFlights(fact.missions).map(([program, list]) => (
                  <span key={program} className="astronaut-program">
                    <span className="astronaut-program-name">{program}</span>
                    {list.map((m) => {
                      const n = /^Apollo (\d+)$/.exec(m)?.[1]
                      const mission = n && findMission(n.padStart(2, '0'))
                      return mission && mission.status !== 'soon' ? (
                        <Link key={m} to={`/mission/${mission.id}`} className="astronaut-flight">
                          {m}
                        </Link>
                      ) : (
                        <span key={m} className="astronaut-flight">
                          {m}
                        </span>
                      )
                    })}
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>
      )}

      <p className="astronaut-bio">{person.bio}</p>

      <section className="astronaut-section">
        <h3>On Apollo</h3>
        <ul className="astronaut-roles">
          {person.apollo.map((a) => {
            const mission = findMission(a.mission)
            return (
              <li key={`${a.mission}-${a.role}`}>
                <Link to={`/mission/${a.mission}`}>{mission?.name || `Apollo ${Number(a.mission)}`}</Link>
                <span>{a.role}</span>
              </li>
            )
          })}
        </ul>
      </section>

      <section className="astronaut-section">
        <h3>Books</h3>
        {person.books.length === 0 ? (
          <p className="astronaut-none">We don&apos;t know of a book-length autobiography or biography.</p>
        ) : (
          <ul className="astronaut-books">
            {person.books.map((b) => (
              <li key={b.title}>
                <a href={b.ol} target="_blank" rel="noreferrer">
                  <cite>{b.title}</cite>
                </a>
                <span>
                  {b.year} · {b.kind}
                  {b.by && ` · ${b.by}`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="astronaut-more">
        <a href={person.wikipedia} target="_blank" rel="noreferrer">
          Read more on Wikipedia ↗
        </a>
      </p>

      <ReportIssueButton
        title={`Astronaut bio: ${person.name} looks wrong`}
        body={`What's wrong with the ${person.name} page?\n\n(current text)\n${person.bio}`}
      >
        Report an inaccuracy
      </ReportIssueButton>
    </div>
  )
}
