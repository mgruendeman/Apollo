import MissionCard from '../components/MissionCard'
import { missions, alreadyCovered } from '../data/missions'

export default function Home() {
  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">GET 000:00:00 — a work in progress</p>
        <h1>Apollo Audio Archive</h1>
        <p className="lede">
          Key moments from the Apollo lunar missions, told in the astronauts'
          own voices — cleaned up and pulled from the original NASA mission
          recordings.
        </p>
        <p className="lede-note">
          <a href={alreadyCovered.url} target="_blank" rel="noreferrer">
            {alreadyCovered.label}
          </a>{' '}
          are already covered second-by-second by{' '}
          <a href={alreadyCovered.url} target="_blank" rel="noreferrer">
            Apollo in Real Time
          </a>
          . This is a starting point for the other lunar missions.
        </p>
      </header>

      <section className="mission-grid">
        {missions.map((mission) => (
          <MissionCard key={mission.id} mission={mission} />
        ))}
      </section>

      <footer className="site-footer">
        <p>
          Audio and transcripts sourced from the Apollo Flight Journal and
          Apollo Lunar Surface Journal, public-domain NASA recordings
          archived at{' '}
          <a href="https://apollojournals.org" target="_blank" rel="noreferrer">
            apollojournals.org
          </a>
          . Each clip links back to its source page.
        </p>
      </footer>
    </div>
  )
}
