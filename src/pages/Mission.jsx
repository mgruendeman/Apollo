import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams, Navigate } from 'react-router-dom'
import AudioPlayer from '../components/AudioPlayer'
import TranscriptPanel from '../components/TranscriptPanel'
import MissionPhaseDiagram from '../components/MissionPhaseDiagram'
import MissionTimeline from '../components/MissionTimeline'
import GlossaryPanel from '../components/GlossaryPanel'
import ReportIssueButton from '../components/ReportIssueButton'
import { findMission } from '../data/missions'
import { classifyPhase } from '../data/phases'
import { getLiveStatus, formatGet } from '../lib/liveStatus'
import { SOURCE_PREFIX_RE } from '../lib/sourceLabel'

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

      <MissionTimeline
        mission={mission}
        clips={clips}
        transcripts={transcripts}
        activeIndex={activeIndex}
        onSelect={selectClip}
      />

      <GlossaryPanel entry={activeGlossaryEntry} onClose={() => setActiveGlossaryEntry(null)} />
    </div>
  )
}
