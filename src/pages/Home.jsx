import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import MissionCard from '../components/MissionCard'
import { missions } from '../data/missions'
import { getAllLiveMissions, formatGet } from '../lib/liveStatus'

export default function Home() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(id)
  }, [])

  const liveMissions = useMemo(() => getAllLiveMissions(missions, now), [now])

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">GET 000:00:00 — a work in progress</p>
        <h1>Apollo Audio Archive</h1>
        <p className="lede">
          The Apollo lunar missions, told in the astronauts' own voices —
          thousands of clips across all eleven flights, from launch to
          splashdown, pulled straight from the original NASA recordings.
        </p>
        <nav className="home-nav">
          <Link to="/glossary" className="glossary-nav-link">
            Browse the glossary ↗
          </Link>
          <Link to="/astronauts" className="glossary-nav-link">
            Meet the astronauts ↗
          </Link>
          <Link to="/guide" className="glossary-nav-link">
            How to use this site ↗
          </Link>
          <Link to="/contact" className="glossary-nav-link">
            Contact &amp; suggestions ↗
          </Link>
        </nav>
      </header>

      {liveMissions.length > 0 && (
        <section className="live-banner-row">
          {liveMissions.map(({ mission, getSeconds, yearsAgo }) => (
            <Link
              key={mission.id}
              to={`/mission/${mission.id}?live=1`}
              className="live-banner"
            >
              <span className="live-dot" />
              <span>
                Happening right now, {yearsAgo} year{yearsAgo === 1 ? '' : 's'}{' '}
                ago: <strong>{mission.name}</strong> is at GET{' '}
                {formatGet(getSeconds)} — jump in
              </span>
            </Link>
          ))}
        </section>
      )}

      <section className="mission-grid">
        {missions.map((mission) => (
          <MissionCard key={mission.id} mission={mission} />
        ))}
      </section>

      <footer className="site-footer">
        <p>
          Edited transcripts and photos © Apollo Audio Archive: free for non-commercial use with credit;{' '}
          <Link to="/guide">see how you can use them</Link>. NASA&apos;s original recordings, transcripts and photographs
          are in the public domain.
        </p>
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
