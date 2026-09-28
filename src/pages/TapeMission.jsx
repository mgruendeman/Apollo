import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import TapePlayer from '../components/TapePlayer'
import TapeTimeline from '../components/TapeTimeline'
import MissionOverview from '../components/MissionOverview'
import ArchiveRecordings from '../components/ArchiveRecordings'
import ListenerFavorites from '../components/ListenerFavorites'
import PhotoGallery from '../components/PhotoGallery'
import GlossaryPanel from '../components/GlossaryPanel'
import { archiveRecordings } from '../data/archiveRecordings'
import { usePlayer } from '../audio/PlayerContext'
import { getLiveStatus, formatGet } from '../lib/liveStatus'
import { chapterTitle, parseGet, tapePhaseAt } from '../lib/missionIndex'
import { formatGetSigned, useMissionTape, withoutAnnouncer } from '../lib/missionTape'

const COMMENTARY_KEY = 'apollo-commentary'
function readCommentary() {
  try {
    return localStorage.getItem(COMMENTARY_KEY) !== 'off'
  } catch {
    return true
  }
}

const endOf = (s) => s.get + (s.to - s.from) * s.rate

// A mission played end to end from NASA's own tapes, with NASA's transcript
// timed to them (public/timeline/<id>.json).
export default function TapeMission({ mission }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [rawTimeline, setRawTimeline] = useState(null)
  const [commentary, setCommentary] = useState(readCommentary)
  const [activeGlossaryEntry, setActiveGlossaryEntry] = useState(null)
  const [now, setNow] = useState(() => new Date())
  const playerRef = useRef(null)
  const player = usePlayer()

  const timeline = useMemo(() => (commentary ? rawTimeline : withoutAnnouncer(rawTimeline)), [rawTimeline, commentary])
  const tape = useMissionTape(timeline, mission.number)

  function toggleCommentary() {
    const next = !commentary
    try {
      localStorage.setItem(COMMENTARY_KEY, next ? 'on' : 'off')
    } catch {
      /* just for this visit */
    }
    setCommentary(next)
  }

  useEffect(() => {
    let canceled = false
    fetch(`${import.meta.env.BASE_URL}timeline/${mission.timeline}.json`)
      .then((r) => r.json())
      .then((data) => !canceled && setRawTimeline(data))
      .catch(() => {})
    return () => {
      canceled = true
    }
  }, [mission])

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

  // Where to start, once the tapes are known: ?at=<seconds> (the reviewer's
  // transcript list links here), ?live=1 (the home page's "happening right
  // now"), or else a few minutes before liftoff.
  const cued = useRef(false)
  useEffect(() => {
    if (!timeline || cued.current) return
    cued.current = true
    const at = searchParams.get('at')
    const status = searchParams.get('live') === '1' ? getLiveStatus(mission, new Date()) : null
    if (at !== null) tape.seek(Number(at), false)
    else if (status) {
      tape.setRealTime(true)
      tape.seek(status.getSeconds, false)
    } else tape.seek(Math.max(timeline.segments[0].get, -300), false)
    if (at !== null || searchParams.has('live')) {
      searchParams.delete('at')
      searchParams.delete('live')
      setSearchParams(searchParams, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeline])

  // One thing plays at a time: the tapes or a recording from the list below.
  useEffect(() => {
    if (tape.playing && player.playing) player.toggle()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tape.playing])
  useEffect(() => {
    if (player.playing && tape.playing) tape.pause()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [player.playing])

  const seekAndShow = useCallback(
    (g) => {
      tape.seek(g, true)
      playerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },
    [tape],
  )

  const liveStatus = getLiveStatus(mission, now)
  const archive = archiveRecordings[mission.id]
  const phase = tapePhaseAt(mission, tape.get)
  const recordedHours = rawTimeline ? rawTimeline.segments.reduce((sum, s) => sum + (s.to - s.from), 0) / 3600 : 0

  function jumpToLive() {
    const status = getLiveStatus(mission, new Date())
    if (!status) return
    tape.setRealTime(true)
    tape.seek(status.getSeconds, true)
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
        {rawTimeline && (
          <p className="clip-stats">
            {Math.round(recordedHours)} hours of NASA&apos;s tapes · GET {formatGetSigned(rawTimeline.segments[0].get)} to{' '}
            {formatGetSigned(Math.max(...rawTimeline.segments.map(endOf)))}
          </p>
        )}
        {liveStatus && (
          <button type="button" className="live-badge" onClick={jumpToLive}>
            <span className="live-dot" />
            Happening right now, {liveStatus.yearsAgo} year
            {liveStatus.yearsAgo === 1 ? '' : 's'} ago — GET {formatGet(liveStatus.getSeconds)}
          </button>
        )}
      </header>

      <MissionOverview mission={mission} />

      {mission.highlights && (
        <section className="highlights-row">
          {mission.highlights.map((h) => (
            <button key={h.id} type="button" className="highlight-chip" onClick={() => seekAndShow(parseGet(h.at))}>
              {h.title}
            </button>
          ))}
        </section>
      )}

      <ListenerFavorites missionId={mission.id} tapesOnly onPick={(_, get) => get && seekAndShow(parseGet(get))} />

      <section className="player-section" ref={playerRef}>
        {timeline ? (
          <TapePlayer
            mission={mission}
            tape={tape}
            lines={timeline.lines}
            start={Math.min(0, timeline.segments[0].get)}
            end={mission.durationSeconds}
            phase={phase}
            chapter={chapterTitle(tape.get, phase)}
            announcer={commentary}
            onAnnouncer={toggleCommentary}
            onTermClick={setActiveGlossaryEntry}
          />
        ) : (
          <p className="loading">Loading {mission.name}&apos;s tapes…</p>
        )}
      </section>

      {rawTimeline && <TapeTimeline mission={mission} timeline={rawTimeline} get={tape.get} onSeek={seekAndShow} />}

      {archive && <ArchiveRecordings mission={mission} archive={archive} />}

      <PhotoGallery mission={mission} />

      <GlossaryPanel
        entry={activeGlossaryEntry}
        onClose={() => setActiveGlossaryEntry(null)}
        onTermClick={setActiveGlossaryEntry}
      />
    </div>
  )
}
