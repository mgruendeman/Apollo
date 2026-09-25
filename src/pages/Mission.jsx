import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams, Navigate } from 'react-router-dom'
import AudioPlayer from '../components/AudioPlayer'
import TranscriptPanel from '../components/TranscriptPanel'
import TapePlayer from '../components/TapePlayer'
import MissionPhaseDiagram from '../components/MissionPhaseDiagram'
import MissionTimeline from '../components/MissionTimeline'
import MissionPhoto from '../components/MissionPhoto'
import MissionOverview from '../components/MissionOverview'
import ArchiveRecordings from '../components/ArchiveRecordings'
import ImmersiveView from '../components/ImmersiveView'
import ListenerFavorites from '../components/ListenerFavorites'
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
import { buildChapters } from '../lib/missionIndex'
import { useMissionTape, withJournalFill, withoutAnnouncer } from '../lib/missionTape'

// The journals' "-pao" clips are the public broadcast: the crew's voices
// with NASA's announcer talking in between (and sometimes over them). Those
// that a plain air-to-ground clip mostly covers can be skipped; the rest are
// the only recording of their moment and stay.
const isPao = (c) => /[-_.]?pao(\b|_|$)/i.test(c.id)
function coveredPao(clips) {
  const ag = clips.filter((c) => !isPao(c)).map((c) => [c.getSeconds, c.getSeconds + (c.durationSeconds || 0)])
  const out = new Set()
  for (const c of clips) {
    if (!isPao(c) || !c.durationSeconds) continue
    const s = c.getSeconds, e = s + c.durationSeconds
    let covered = 0
    for (const [a, b] of ag) covered += Math.max(0, Math.min(e, b) - Math.max(s, a))
    if (covered / (e - s) >= 0.8) out.add(c.id)
  }
  return out
}
const COMMENTARY_KEY = 'apollo-commentary'
function readCommentary() {
  try {
    return localStorage.getItem(COMMENTARY_KEY) !== 'off'
  } catch {
    return true
  }
}

const LISTEN_KEY = 'apollo-listen'
const FILL_KEY = 'apollo-journal-fill'
function readListen() {
  try {
    return localStorage.getItem(LISTEN_KEY) || 'tapes'
  } catch {
    return 'tapes'
  }
}
const toSeconds = (get) => {
  const neg = get.startsWith('-')
  const [h, m, s] = get.replace('-', '').split(':').map(Number)
  return (neg ? -1 : 1) * (h * 3600 + m * 60 + s)
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
  const [allClips, setClips] = useState(null)
  const [commentary, setCommentary] = useState(readCommentary)
  const skippable = useMemo(() => (allClips ? coveredPao(allClips) : new Set()), [allClips])
  // The site's own index: each clip carries its flight phase and chapter
  // ("Day 3 · Translunar Coast").
  const clips = useMemo(() => {
    const base = allClips && !commentary ? allClips.filter((c) => !skippable.has(c.id)) : allClips
    if (!base) return base
    const chapters = buildChapters(base, computePhases(base, mission.durationSeconds, mission.landingSeconds))
    const out = [...base]
    for (const ch of chapters)
      for (let i = ch.startIndex; i < ch.endIndex; i++) out[i] = { ...base[i], phase: ch.phase, chapterTitle: ch.title }
    return out
  }, [allClips, commentary, skippable, mission])
  function toggleCommentary() {
    const next = !commentary
    try {
      localStorage.setItem(COMMENTARY_KEY, next ? 'on' : 'off')
    } catch {
      /* just for this visit */
    }
    setCommentary(next)
  }
  const [transcripts, setTranscripts] = useState(null)
  const player = usePlayer()
  const [cuedIndex, setCuedIndex] = useState(0)
  const [immersive, setImmersive] = useState(false)
  const closeImmersive = useCallback(() => setImmersive(false), [])
  const [activeGlossaryEntry, setActiveGlossaryEntry] = useState(null)
  const [now, setNow] = useState(() => new Date())
  const didAutoJump = useRef(false)
  const playerRef = useRef(null)

  // Whole-mission playback from NASA's tapes, where a mission has them.
  const [rawTimeline, setRawTimeline] = useState(null)
  const [listen, setListenState] = useState(readListen)
  const [fill, setFillState] = useState(() => {
    try {
      return localStorage.getItem(FILL_KEY) !== 'off'
    } catch {
      return true
    }
  })
  function setFill(next) {
    try {
      localStorage.setItem(FILL_KEY, next ? 'on' : 'off')
    } catch {
      /* just for this visit */
    }
    setFillState(next)
  }
  const timeline = useMemo(() => {
    const filled = fill ? withJournalFill(rawTimeline, clips) : rawTimeline
    return commentary ? filled : withoutAnnouncer(filled)
  }, [rawTimeline, clips, fill, commentary])
  const tape = useMissionTape(timeline, mission?.number)
  const tapeMode = !!timeline && listen === 'tapes'
  function setListen(next) {
    try {
      localStorage.setItem(LISTEN_KEY, next)
    } catch {
      /* just for this visit */
    }
    if (next === 'clips') tape.pause()
    else if (player.playing) player.toggle()
    setListenState(next)
  }

  useEffect(() => {
    if (!mission?.timeline) return undefined
    let canceled = false
    fetch(`${import.meta.env.BASE_URL}timeline/${mission.timeline}.json`)
      .then((r) => r.json())
      .then((data) => !canceled && setRawTimeline(data))
      .catch(() => {})
    return () => {
      canceled = true
    }
  }, [mission])

  // Start the tapes a few minutes before liftoff.
  const tapeCued = useRef(false)
  useEffect(() => {
    if (!timeline || tapeCued.current) return
    tapeCued.current = true
    tape.seek(Math.max(timeline.segments[0].get, -300), false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeline])

  // One thing plays at a time: the tapes or the journal's clips.
  useEffect(() => {
    if (tape.playing && player.playing) player.toggle()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tape.playing])
  useEffect(() => {
    if (player.playing && tape.playing) tape.pause()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [player.playing])

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!mission?.clipsFile) return
    let canceled = false
    import(`../data/clips/${mission.clipsFile}.json`).then((mod) => {
      if (!canceled) setClips(mod.default)
    })
    return () => {
      canceled = true
    }
  }, [mission])

  // Transcripts are fetched as a static asset (not bundled) so the clip
  // index — needed for first paint — isn't held up by a multi-MB file the
  // player doesn't need until a line is due to be shown.
  useEffect(() => {
    if (!mission?.clipsFile) return
    let canceled = false
    fetch(`${import.meta.env.BASE_URL}transcripts/${mission.clipsFile}.json`)
      .then((r) => r.json())
      .then((data) => {
        if (!canceled) setTranscripts(data)
      })
      .catch(() => {})
    return () => {
      canceled = true
    }
  }, [mission])

  const liveStatus = mission ? getLiveStatus(mission, now) : null
  const phases = useMemo(() => (clips ? clips.map((c) => c.phase) : []), [clips])
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
    if (status && mission.timeline && readListen() === 'tapes') {
      tape.setRealTime(true)
      tape.seek(status.getSeconds, false)
    } else if (status) {
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

  // Picking a clip further down the page (the timeline) brings the player
  // and its transcript into view.
  function selectFromTimeline(i) {
    if (tapeMode) tape.seek(clips[i].getSeconds, true)
    else selectClip(i)
    playerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
    if (i === -1) return
    if (tapeMode) tape.seek(clips[i].getSeconds, true)
    else selectClip(i)
  }

  function jumpToLive() {
    const status = getLiveStatus(mission, new Date())
    if (!status) return
    if (tapeMode) {
      tape.setRealTime(true)
      tape.seek(status.getSeconds, true)
    } else selectClip(nearestClipIndex(clips, status.getSeconds))
  }

  // The journal clip at (or last before) the tapes' position: its phase and chapter.
  let tapeClipIndex = 0
  if (tapeMode) while (tapeClipIndex + 1 < clips.length && clips[tapeClipIndex + 1].getSeconds <= tape.get) tapeClipIndex++

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
        {skippable.size > 0 && !tapeMode && (
          <label className="commentary-toggle">
            <input type="checkbox" checked={commentary} onChange={toggleCommentary} />
            Mission Control announcer
            <span>
              {commentary
                ? `On: includes ${skippable.size} broadcast clips where the announcer talks between (and over) the crew.`
                : `Off: those ${skippable.size} clips are skipped for the plain air-to-ground recording. Moments with only the broadcast recording keep it.`}
            </span>
          </label>
        )}
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

      <ListenerFavorites
        missionId={mission.id}
        onPick={(id, get) => {
          if (id.startsWith('tapes-') && get) {
            if (!tapeMode) setListen('tapes')
            tape.seek(toSeconds(get), true)
            playerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            return
          }
          const i = clips.findIndex((c) => c.id === id)
          if (i === -1) return
          if (tapeMode) setListen('clips')
          selectClip(i)
          playerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }}
      />

      <section className="player-section" ref={playerRef}>
        {timeline && (
          <div className="listen-switch" role="tablist" aria-label="How to listen">
            <button type="button" role="tab" aria-selected={tapeMode} onClick={() => setListen('tapes')}>
              Whole mission
              <span>NASA's tapes, end to end</span>
            </button>
            <button type="button" role="tab" aria-selected={!tapeMode} onClick={() => setListen('clips')}>
              Highlight clips
              <span>{clips.length} moments, with photos</span>
            </button>
          </div>
        )}
        {tapeMode ? (
          <TapePlayer
            mission={mission}
            tape={tape}
            lines={timeline.lines}
            start={Math.min(0, timeline.segments[0].get)}
            end={mission.durationSeconds}
            phase={phases[tapeClipIndex]}
            fill={fill}
            onFill={setFill}
            announcer={commentary}
            onAnnouncer={toggleCommentary}
            chapter={clips[tapeClipIndex].chapterTitle}
            clips={clips}
            clipIndex={tapeClipIndex}
            onTermClick={setActiveGlossaryEntry}
          />
        ) : (
        <>
        <div className="player-top">
          <div className="player-top-text">
            <p className="get-clock">GET {moment.get}</p>
            <h2>{moment.chapterTitle}</h2>
            <button type="button" className="immersive-open" onClick={() => setImmersive(true)}>
              ⛶ Full-screen view
            </button>
          </div>
          <MissionPhaseDiagram phase={phase} mission={mission} />
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
            mission={mission.id}
            clip={moment.id}
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
        </>
        )}
      </section>

      <MissionTimeline
        mission={mission}
        clips={clips}
        transcripts={transcripts}
        phases={phases}
        activeIndex={activeIndex}
        onSelect={selectFromTimeline}
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
