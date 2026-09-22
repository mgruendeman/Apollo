import { Link, useParams } from 'react-router-dom'
import { astronauts } from '../data/astronauts'
import { findMission } from '../data/missions'
import { speakerAvatar } from '../data/speakers'
import ReportIssueButton from '../components/ReportIssueButton'

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
