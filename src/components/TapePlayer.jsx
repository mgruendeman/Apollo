import { useEffect, useMemo, useState } from 'react'
import TranscriptPanel from './TranscriptPanel'
import MissionPhaseDiagram from './MissionPhaseDiagram'
import { formatGetSigned, tapeUrl } from '../lib/missionTape'

const hourOf = (g) => Math.floor(g / 3600)
const tapeClip = (h) => `tapes-h${h}`

// The whole mission from NASA's tapes: one scrubber for all ~8 days, the
// recorded pieces shaded, and NASA's transcript following along an hour at
// a time. `tape` is useMissionTape()'s state and controls.
export default function TapePlayer({ mission, tape, lines, start, end, phase, chapter, onTermClick }) {
  const [drag, setDrag] = useState(null)
  const shown = drag ?? tape.get
  const span = end - start

  // NASA's lines by hour of the mission; the transcript shows the hour playing.
  const byHour = useMemo(() => {
    const out = new Map()
    for (const l of lines || []) {
      const h = hourOf(l.g)
      if (!out.has(h)) out.set(h, [])
      out.get(h).push({ get: formatGetSigned(l.g), offsetSeconds: l.g, speaker: l.s, text: l.t })
    }
    return out
  }, [lines])
  const hour = hourOf(tape.get)
  const hourLines = byHour.get(hour) || []

  const piece = tape.piece
  const source = tape.inGap ? null : piece?.journal
    ? { label: 'Apollo Flight Journal clip (the tapes have a gap here)', href: piece.url }
    : piece && { label: `NASA tape ${piece.tape}`, href: `https://archive.org/details/Apollo${mission.number}Audio` }

  useEffect(() => {
    if (!tape.playing || !('mediaSession' in navigator)) return
    navigator.mediaSession.metadata = new MediaMetadata({
      title: `GET ${formatGetSigned(tape.get).slice(0, -3)} · whole mission`,
      artist: mission.name,
      album: 'Apollo Audio Archive',
    })
    navigator.mediaSession.setActionHandler('play', tape.toggle)
    navigator.mediaSession.setActionHandler('pause', tape.pause)
    navigator.mediaSession.setActionHandler('previoustrack', null)
    navigator.mediaSession.setActionHandler('nexttrack', null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tape.playing, hour, mission])

  function commit(e) {
    if (drag == null) return
    tape.seek(Number(e.currentTarget.value))
    setDrag(null)
  }

  return (
    <>
      <div className="player-top">
        <div className="player-top-text">
          <p className="get-clock">GET {formatGetSigned(shown)}</p>
          <h2>{chapter}</h2>
          {tape.inGap && <p className="tape-gap-note">No recording here: real time counting on to the next one.</p>}
          {source && (
            <a className="source-link" href={source.href} target="_blank" rel="noreferrer">
              {source.label} ↗
            </a>
          )}
        </div>
        <MissionPhaseDiagram phase={phase} />
      </div>

      <div className="tape-player">
        <button
          type="button"
          className="play-button"
          onClick={tape.toggle}
          aria-label={tape.playing ? 'Pause' : 'Play'}
        >
          {tape.loading && tape.playing ? '…' : tape.playing ? '❚❚' : '▶'}
        </button>
        <div className="tape-scrub">
          <svg viewBox={`0 0 ${span} 10`} preserveAspectRatio="none" aria-hidden="true">
            {tape.segments.map((s, i) => (
              <rect
                key={i}
                className={s.journal ? 'tape-piece is-journal' : 'tape-piece'}
                x={s.get - start}
                width={Math.max((s.to - s.from) * s.rate, span / 2000)}
                y="0"
                height="10"
              />
            ))}
            <rect className="tape-played" x="0" width={Math.max(0, shown - start)} y="4" height="2" />
          </svg>
          <input
            type="range"
            min={start}
            max={end}
            step="1"
            value={Math.min(end, Math.max(start, shown))}
            aria-label="Mission time"
            onChange={(e) => setDrag(Number(e.target.value))}
            onPointerUp={commit}
            onKeyUp={commit}
            onBlur={commit}
          />
        </div>
        <div className="tape-skip">
          <button type="button" onClick={() => tape.seek(tape.get - 30)} aria-label="Back 30 seconds">
            −30s
          </button>
          <button type="button" onClick={() => tape.seek(tape.get + 30)} aria-label="Forward 30 seconds">
            +30s
          </button>
        </div>
      </div>

      <label className="commentary-toggle">
        <input type="checkbox" checked={tape.realTime} onChange={(e) => tape.setRealTime(e.target.checked)} />
        Real time
        <span>
          {tape.realTime
            ? 'On: silent stretches between recordings count by at their true length, as they happened.'
            : 'Off: silent stretches between recordings are skipped.'}
        </span>
      </label>

      {hourLines.length > 0 ? (
        <TranscriptPanel
          key={`tape-hour-${hour}`}
          lines={hourLines}
          currentTime={tape.get}
          onTermClick={onTermClick}
          onLineSeek={(g) => tape.seek(g, true)}
          report={{
            missionName: mission.name,
            clipId: `${tapeClip(hour)} (whole-mission tapes)`,
            audioUrl: piece && (piece.url || tapeUrl(mission.number, piece.tape)),
            sourceUrl: source?.href,
          }}
          mission={mission.id}
          clip={tapeClip(hour)}
        />
      ) : (
        <p className="moment-description">No transcript for this hour of the mission.</p>
      )}
    </>
  )
}
