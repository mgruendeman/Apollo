import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams, Navigate } from 'react-router-dom'
import AudioPlayer from '../components/AudioPlayer'
import TranscriptPanel from '../components/TranscriptPanel'
import MissionPhaseDiagram from '../components/MissionPhaseDiagram'
import GlossaryPanel from '../components/GlossaryPanel'
import ReportIssueButton from '../components/ReportIssueButton'
import { findMission } from '../data/missions'
import { classifyPhase } from '../data/phases'
import { classifyEventType, EVENT_TYPE_META } from '../data/eventType'
import { getLiveStatus, formatGet } from '../lib/liveStatus'

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

function nearestClipIndex(clips, getSeconds) {
  let i = clips.findIndex((c) => c.getSeconds >= getSeconds)
  if (i === -1) i = clips.length - 1
  return i
}

export default function Mission() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const mission = findMission(id)
  const [clips, setClips] = useState(null)
  const [transcripts, setTranscripts] = useState(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [autoPlay, setAutoPlay] = useState(false)
  const [continuous, setContinuous] = useState(true)
  const [currentTime, setCurrentTime] = useState(0)
  const [seekRequest, setSeekRequest] = useState(null)
  const [activeGlossaryEntry, setActiveGlossaryEntry] = useState(null)
  const [now, setNow] = useState(() => new Date())
  const didAutoJump = useRef(false)

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

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

  // Transcripts are fetched as a static asset (not bundled) so the clip
  // index — needed for first paint — isn't held up by a multi-MB file the
  // player doesn't need until a line is due to be shown.
  useEffect(() => {
    if (!mission?.clipsFile) return
    let cancelled = false
    fetch(`${import.meta.env.BASE_URL}transcripts/${mission.clipsFile}.json`)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setTranscripts(data)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [mission])

  const chapters = useMemo(() => (clips ? buildChapters(clips) : []), [clips])
  const liveStatus = mission ? getLiveStatus(mission, now) : null

  // Coming in from the home page's "happening right now" banner: jump to
  // wherever the mission actually is at this instant, once, as soon as the
  // clip index is ready.
  useEffect(() => {
    if (!clips || didAutoJump.current || searchParams.get('live') !== '1') return
    didAutoJump.current = true
    const status = getLiveStatus(mission, new Date())
    if (status) {
      setActiveIndex(nearestClipIndex(clips, status.getSeconds))
    }
    searchParams.delete('live')
    setSearchParams(searchParams, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clips])

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
  const activeLines = transcripts?.[moment.id] || []
  const activeChapterIndex = chapters.findIndex(
    (ch) => activeIndex >= ch.startIndex && activeIndex < ch.endIndex,
  )
  const phase = classifyPhase(moment.sourceLabel)

  function selectClip(i) {
    setActiveIndex(i)
    setAutoPlay(true)
    setCurrentTime(0)
  }

  function handleEnded() {
    if (continuous && activeIndex < clips.length - 1) {
      selectClip(activeIndex + 1)
    } else {
      setAutoPlay(false)
    }
  }

  function jumpToHighlight(id) {
    const i = clips.findIndex((c) => c.id === id)
    if (i !== -1) selectClip(i)
  }

  function jumpToLive() {
    const status = getLiveStatus(mission, new Date())
    if (status) selectClip(nearestClipIndex(clips, status.getSeconds))
  }

  function previewFor(c) {
    const lines = transcripts?.[c.id]
    if (lines && lines.length) return `${lines[0].speaker}: ${lines[0].text}`
    return null
  }

  // A chapter that happens to contain one of the mission's curated
  // highlight clips gets that highlight's opening line shown as a
  // pull-quote, so the timeline surfaces its "big moments" at a glance
  // instead of requiring you to open every chapter to find them.
  function highlightFor(ch) {
    if (!mission.highlights) return null
    const hit = mission.highlights.find((h) => {
      const idx = clips.findIndex((c) => c.id === h.id)
      return idx >= ch.startIndex && idx < ch.endIndex
    })
    if (!hit) return null
    const lines = transcripts?.[hit.id]
    return { title: hit.title, quote: lines?.[0]?.text }
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
        {liveStatus && (
          <button type="button" className="live-badge" onClick={jumpToLive}>
            <span className="live-dot" />
            Happening right now, {liveStatus.yearsAgo} year
            {liveStatus.yearsAgo === 1 ? '' : 's'} ago — GET{' '}
            {formatGet(liveStatus.getSeconds)}
          </button>
        )}
      </header>

      {mission.highlights && (
        <section className="highlights-row">
          {mission.highlights.map((h) => (
            <button
              key={h.title}
              type="button"
              className="highlight-chip"
              onClick={() => jumpToHighlight(h.id)}
            >
              {h.title}
            </button>
          ))}
        </section>
      )}

      <section className="player-section">
        <div className="player-top">
          <div className="player-top-text">
            <p className="get-clock">GET {moment.get}</p>
            <h2>{moment.sourceLabel.replace(SOURCE_PREFIX_RE, '')}</h2>
          </div>
          <MissionPhaseDiagram phase={phase} />
        </div>
        <AudioPlayer
          key={`player-${moment.id}`}
          moment={moment}
          title={moment.sourceLabel.replace(SOURCE_PREFIX_RE, '')}
          missionName={mission.name}
          autoPlay={autoPlay}
          onEnded={handleEnded}
          onNext={() => selectClip(activeIndex + 1)}
          onPrevious={() => selectClip(activeIndex - 1)}
          hasNext={activeIndex < clips.length - 1}
          hasPrevious={activeIndex > 0}
          onTimeUpdate={setCurrentTime}
          seekRequest={seekRequest}
        />
        {activeLines.length > 0 ? (
          <TranscriptPanel
            key={`transcript-${moment.id}`}
            lines={activeLines}
            currentTime={currentTime}
            onTermClick={setActiveGlossaryEntry}
            onLineSeek={(seconds) => setSeekRequest({ seconds })}
          />
        ) : (
          <p className="moment-description">
            {transcripts ? 'No transcript for this clip.' : 'Loading transcript…'}
          </p>
        )}
        <div className="player-controls-row">
          <label className="continuous-toggle">
            <input
              type="checkbox"
              checked={continuous}
              onChange={(e) => setContinuous(e.target.checked)}
            />
            Keep playing through the mission
          </label>
          <span className="player-links">
            <a
              className="source-link"
              href={moment.sourceUrl}
              target="_blank"
              rel="noreferrer"
            >
              Full transcript ↗
            </a>
            <ReportIssueButton
              title={`${mission.name} GET ${moment.get}: audio/transcript issue`}
              body={`Clip: ${moment.id}\nGET: ${moment.get}\nSource: ${moment.sourceUrl}\nAudio: ${moment.audioUrl}\n\nWhat's wrong?\n`}
            >
              Report an issue with this clip
            </ReportIssueButton>
          </span>
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
        <p className="timeline-legend">
          <span className="legend-item">★ major milestone</span>
          <span className="legend-item">☾ rest / routine period</span>
        </p>
        {chapters.map((ch, ci) => {
          const count = ch.endIndex - ch.startIndex
          const eventType = classifyEventType(ch.label)
          const meta = EVENT_TYPE_META[eventType]
          const highlight = highlightFor(ch)
          return (
            <details
              key={ch.startIndex}
              open={ci === activeChapterIndex}
              className={meta.className}
            >
              <summary>
                <span className="chapter-get">{clips[ch.startIndex].get}</span>
                {meta.icon && <span className="chapter-icon">{meta.icon}</span>}
                <span className="chapter-label">
                  {ch.label.replace(SOURCE_PREFIX_RE, '')}
                </span>
                <span className="chapter-count">
                  {count} clip{count === 1 ? '' : 's'}
                </span>
              </summary>
              {highlight && (
                <blockquote className="chapter-quote">
                  <p className="chapter-quote-title">{highlight.title}</p>
                  {highlight.quote && <p>"{highlight.quote}"</p>}
                </blockquote>
              )}
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
                          {(previewFor(c) || ch.label).slice(0, 100)}
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

      <GlossaryPanel entry={activeGlossaryEntry} onClose={() => setActiveGlossaryEntry(null)} />
    </div>
  )
}
