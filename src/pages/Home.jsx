import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import MissionCard from '../components/MissionCard'
import { missions } from '../data/missions'
import { getAllLiveMissions, formatGet } from '../lib/liveStatus'
import logo from '../assets/logo/apollo-rewind.webp'

// "Apollo 11, 12 and 14"
function listOf(ms) {
  const n = ms.map((m) => m.number)
  return `Apollo ${n.length > 1 ? `${n.slice(0, -1).join(', ')} and ${n[n.length - 1]}` : n[0]}`
}

export default function Home() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(id)
  }, [])

  const liveMissions = useMemo(() => getAllLiveMissions(missions, now), [now])
  const [firstVisit] = useState(() => {
    try {
      return !localStorage.getItem('apollo-opened-mission')
    } catch {
      return false
    }
  })
  const onTapes = listOf(missions.filter((m) => m.timeline))
  const onClips = listOf(missions.filter((m) => m.clipsFile && !m.timeline))

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">GET 000:00:00 — a work in progress</p>
        <h1 className="hero-logo">
          <img src={logo} alt="Apollo Rewind" width="1200" height="571" />
        </h1>
        <p className="lede">
          The Apollo Moon missions in the astronauts&apos; own voices. {onTapes} play end to end from NASA&apos;s own
          tapes, launch to splashdown, with the conversation written out alongside. The other flights have clips of
          their key moments while I work through their tapes.
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

      {firstVisit && (
        <p className="start-tip">
          <span aria-hidden="true">👋</span> New here? Pick a mission below to start listening. <strong>Apollo 11</strong>, the
          first landing, is a good place to begin.
        </p>
      )}
      <h2 className="mission-grid-title">Pick a mission to listen</h2>
      <section className="mission-grid">
        {missions.map((mission) => (
          <MissionCard key={mission.id} mission={mission} />
        ))}
      </section>

      <footer className="site-footer">
        <p>
          Edited transcripts and photos © Apollo Rewind: free for non-commercial use with credit;{' '}
          <Link to="/guide">see how you can use them</Link>. NASA&apos;s original recordings, transcripts and photographs
          are in the public domain.
        </p>
        <p>
          {onTapes}: NASA&apos;s tapes and air-to-ground transcripts. {onClips}: clips and transcripts from the Apollo
          Flight Journal and Apollo Lunar Surface Journal, public-domain NASA recordings archived at{' '}
          <a href="https://apollojournals.org" target="_blank" rel="noreferrer">
            apollojournals.org
          </a>
          ; each clip links back to its source page.
        </p>
        <p>Mission emblems: NASA. Apollo Rewind is an independent project, not affiliated with or endorsed by NASA.</p>
      </footer>
    </div>
  )
}
