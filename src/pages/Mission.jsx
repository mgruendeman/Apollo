import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import AudioPlayer from '../components/AudioPlayer'
import { findMission } from '../data/missions'

const SOURCE_PREFIX_RE = /^Apollo \d+ (Flight Journal|Lunar Surface Journal) — /

function buildChapters(clips) {
  const chapters = []
  for (let i = 0; i < clips.length; i++) {
    const label = clips[i].sourceLabel
    const last = chapters[chapters.length - 1]
    if (last && last.label === label) {
      last.endIndex = i + 1
    } else {
      chapters.push({ label, startIndex: i, endIndex: i + 1 })
    }
  }
  return chapters
}

export default function Mission() {
  const { id } = useParams()
  const mission = findMission(id)
  const [clips, setClips] = useState(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [autoPlay, setAutoPlay] = useState(false)
  const [continuous, setContinuous] = useState(true)

  useEffect(() => {
    if (!mission?.clipsFile) return
    let cancelled = false
    import(`../data/clips/${mission.clipsFile}.json`).then((mod) => {
      if (!cancelled) setClips(mod.default)
    })
    return () => {
      cancelled = true
    }
  }, [mission])

  const chapters = useMemo(() => (clips ? buildChapters(clips) : []), [clips])

  if (!mission || mission.status !== 'available') {
    return <Navigate to="/" replace />
  }

  if (!clips) {
    return (
      <div className="page">
        <Link to="/" className="back-link">
          ← All missions
        </Link>
        <p className="loading">Loading {mission.name} audio index…</p>
      </div>
    )
  }

  const moment = clips[activeIndex]
  const activeChapterIndex = chapters.findIndex(
    (ch) => activeIndex >= ch.startIndex && activeIndex < ch.endIndex,
  )

  function selectClip(i) {
    setActiveIndex(i)
    setAutoPlay(true)
  }

  function handleEnded() {
    if (continuous && activeIndex < clips.length - 1) {
      selectClip(activeIndex + 1)
    } else {
      setAutoPlay(false)
    }
  }

  function jumpToHighlight(getSeconds) {
    let i = clips.findIndex((c) => c.getSeconds >= getSeconds)
    if (i === -1) i = clips.length - 1
    selectClip(i)
  }

  return (
    <div className="page">
      <Link to="/" className="back-link">
        ← All missions
      </Link>

      <header className="mission-header">
        <p className="eyebrow">Apollo {mission.number}</p>
        <h1>{mission.name}</h1>
        <p className="mission-header-dates">{mission.dates}</p>
        <p className="mission-header-crew">{mission.crew.join(' · ')}</p>
        <p className="lede">{mission.summary}</p>
        <p className="clip-stats">
          {clips.length} audio clips · GET {clips[0].get} to{' '}
          {clips[clips.length - 1].get}
        </p>
      </header>

      {mission.highlights && (
        <section className="highlights-row">
          {mission.highlights.map((h) => (
            <button
              key={h.title}
              type="button"
              className="highlight-chip"
              onClick={() => jumpToHighlight(h.getSeconds)}
            >
              {h.title}
            </button>
          ))}
        </section>
      )}

      <section className="player-section">
        <p className="get-clock">GET {moment.get}</p>
        <h2>{moment.sourceLabel.replace(SOURCE_PREFIX_RE, '')}</h2>
        <AudioPlayer
          key={moment.id}
          moment={moment}
          autoPlay={autoPlay}
          onEnded={handleEnded}
        />
        <p className="moment-description">
          {moment.context || moment.sourceLabel}
        </p>
        <div className="player-controls-row">
          <label className="continuous-toggle">
            <input
              type="checkbox"
              checked={continuous}
              onChange={(e) => setContinuous(e.target.checked)}
            />
            Keep playing through the mission
          </label>
          <a
            className="source-link"
            href={moment.sourceUrl}
            target="_blank"
            rel="noreferrer"
          >
            Full transcript ↗
          </a>
        </div>
        <div className="prev-next-row">
          <button
            type="button"
            disabled={activeIndex === 0}
            onClick={() => selectClip(activeIndex - 1)}
          >
            ← Previous clip
          </button>
          <button
            type="button"
            disabled={activeIndex === clips.length - 1}
            onClick={() => selectClip(activeIndex + 1)}
          >
            Next clip →
          </button>
        </div>
      </section>

      <section className="timeline">
        <h3>Full mission timeline</h3>
        {chapters.map((ch, ci) => {
          const count = ch.endIndex - ch.startIndex
          return (
            <details key={ch.startIndex} open={ci === activeChapterIndex}>
              <summary>
                <span className="chapter-get">{clips[ch.startIndex].get}</span>
                <span className="chapter-label">
                  {ch.label.replace(SOURCE_PREFIX_RE, '')}
                </span>
                <span className="chapter-count">
                  {count} clip{count === 1 ? '' : 's'}
                </span>
              </summary>
              <ol>
                {clips.slice(ch.startIndex, ch.endIndex).map((c, j) => {
                  const i = ch.startIndex + j
                  return (
                    <li key={c.id}>
                      <button
                        type="button"
                        className={
                          i === activeIndex
                            ? 'moment-item is-active'
                            : 'moment-item'
                        }
                        onClick={() => selectClip(i)}
                      >
                        <span className="moment-get">{c.get}</span>
                        <span className="moment-title">
                          {(c.context || ch.label).slice(0, 100)}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ol>
            </details>
          )
        })}
      </section>
    </div>
  )
}
