import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams, Navigate } from 'react-router-dom'
import AudioPlayer from '../components/AudioPlayer'
import TranscriptPanel from '../components/TranscriptPanel'
import MissionPhaseDiagram from '../components/MissionPhaseDiagram'
import MissionTimeline from '../components/MissionTimeline'
import MissionPhoto from '../components/MissionPhoto'
import MissionOverview from '../components/MissionOverview'
import ArchiveRecordings from '../components/ArchiveRecordings'
import ImmersiveView from '../components/ImmersiveView'
import MomentPhotos from '../components/MomentPhotos'
import PhotoGallery from '../components/PhotoGallery'
import GlossaryPanel from '../components/GlossaryPanel'
import ReportIssueButton from '../components/ReportIssueButton'
import { findMission } from '../data/missions'
import { photosByClipId } from '../data/photos'
import { archiveRecordings } from '../data/archiveRecordings'
import { computePhases } from '../data/phases'
import { usePlayer } from '../audio/PlayerContext'
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
  const player = usePlayer()
  const [cuedIndex, setCuedIndex] = useState(0)
  const [immersive, setImmersive] = useState(false)
  const closeImmersive = useCallback(() => setImmersive(false), [])
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
  const phases = useMemo(
    () => (clips ? computePhases(clips, mission.durationSeconds, mission.landingSeconds) : []),
    [clips, mission],
  )
  // While this mission is the one loaded in the app-wide player, the page
  // follows the player; otherwise it shows its own cued clip.
  const isLoaded = !!mission && player.session?.mission.id === mission.id
  const activeIndex = isLoaded ? player.session.index : cuedIndex

  // Coming in from the home page's "happening right now" banner: jump to
  // wherever the mission actually is at this instant, once, as soon as the
  // clip index is ready.
  useEffect(() => {
    if (!clips || didAutoJump.current || searchParams.get('live') !== '1') return
    didAutoJump.current = true
    const status = getLiveStatus(mission, new Date())
    if (status) {
      const i = nearestClipIndex(clips, status.getSeconds)
      if (isLoaded || !player.playing) player.cue(mission, clips, i)
      else setCuedIndex(i)
    }
    searchParams.delete('live')
    setSearchParams(searchParams, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clips])

  if (!mission || (mission.status !== 'available' && mission.status !== 'archive')) {
    return <Navigate to="/" replace />
  }

  const archive = archiveRecordings[mission.id]

  if (!mission.clipsFile) {
    return (
      <div className="page">
        <Link to="/" className="back-link">
          ← All missions
        </Link>
        <header className="mission-header">
          <p className="eyebrow">Apollo {mission.number}</p>
          <h1>{mission.name}</h1>
          <p className="mission-header-dates">{mission.dates}</p>
          <p className="lede">{mission.summary}</p>
        </header>
        <MissionOverview mission={mission} />
        {archive && <ArchiveRecordings mission={mission} archive={archive} />}
        <PhotoGallery mission={mission} />
      </div>
    )
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
  const phase = phases[activeIndex]
  const currentTime = isLoaded ? player.currentTime : 0
  const lineReportInfo = {
    missionName: mission.name,
    clipId: moment.id,
    audioUrl: moment.audioUrl,
    sourceUrl: moment.sourceUrl,
  }

  function selectClip(i) {
    player.play(mission, clips, i)
  }

  function seekToLine(seconds) {
    if (isLoaded) player.seek(seconds)
    else player.play(mission, clips, activeIndex, seconds)
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

      <MissionOverview mission={mission} />

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
            <button type="button" className="immersive-open" onClick={() => setImmersive(true)}>
              ⛶ Full-screen view
            </button>
          </div>
          <MissionPhaseDiagram phase={phase} />
        </div>
        <AudioPlayer mission={mission} clips={clips} index={activeIndex} />
        <MissionPhoto photo={photosByClipId[moment.id]} />
        <MomentPhotos mission={mission} clip={moment} phase={phase} />
        {activeLines.length > 0 ? (
          <TranscriptPanel
            key={`transcript-${moment.id}`}
            lines={activeLines}
            currentTime={currentTime}
            onTermClick={setActiveGlossaryEntry}
            onLineSeek={seekToLine}
            report={lineReportInfo}
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
              checked={player.continuous}
              onChange={(e) => player.setContinuous(e.target.checked)}
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
        phases={phases}
        activeIndex={activeIndex}
        onSelect={selectClip}
      />

      {archive && <ArchiveRecordings mission={mission} archive={archive} />}

      <PhotoGallery mission={mission} />

      {immersive && (
        <ImmersiveView
          mission={mission}
          clips={clips}
          index={activeIndex}
          lines={activeLines}
          currentTime={currentTime}
          phase={phase}
          highlightPhoto={photosByClipId[moment.id]}
          onClose={closeImmersive}
          onLineSeek={seekToLine}
          report={lineReportInfo}
          onPrevious={activeIndex > 0 ? () => selectClip(activeIndex - 1) : null}
          onNext={activeIndex < clips.length - 1 ? () => selectClip(activeIndex + 1) : null}
        />
      )}

      <GlossaryPanel
        entry={activeGlossaryEntry}
        onClose={() => setActiveGlossaryEntry(null)}
        onTermClick={setActiveGlossaryEntry}
      />
    </div>
  )
}
