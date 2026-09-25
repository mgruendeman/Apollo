import { useCallback, useEffect, useMemo, useState } from 'react'
import ImmersiveView from './ImmersiveView'
import MomentPhotos from './MomentPhotos'
import TranscriptPanel from './TranscriptPanel'
import MissionPhaseDiagram from './MissionPhaseDiagram'
import { formatGetSigned } from '../lib/missionTape'

const hourOf = (g) => Math.floor(g / 3600)
const tapeClip = (h) => `tapes-h${h}`

// The whole mission from NASA's tapes: one scrubber for all ~8 days, the
// recorded pieces shaded, and NASA's transcript following along an hour at
// a time. `tape` is useMissionTape()'s state and controls.
export default function TapePlayer({ mission, tape, lines, start, end, phase, chapter, fill, onFill, announcer, onAnnouncer, onTermClick, clips, clipIndex }) {
  const [drag, setDrag] = useState(null)
  const [immersive, setImmersive] = useState(false)
  const closeImmersive = useCallback(() => setImmersive(false), [])
  const shown = drag ?? tape.get
  const span = end - start

  // NASA's lines by hour of the mission; the transcript shows the hour
  // playing and those either side, so it reads on without a break.
  const byHour = useMemo(() => {
    const out = new Map()
    for (const l of lines || []) {
      if (l.c === 'pao' && !announcer && !l.o) continue   // (where he talks over the crew he can't be cut)
      const h = hourOf(l.g)
      if (!out.has(h)) out.set(h, [])
      out.get(h).push({ get: formatGetSigned(l.g), offsetSeconds: l.g, speaker: l.s, text: l.t, channel: l.c, over: l.o, unheard: l.n, clip: tapeClip(h) })
    }
    return out
  }, [lines, announcer])
  const hour = hourOf(tape.get)
  const hours = [hour - 1, hour, hour + 1].filter((h) => byHour.has(h))
  const shownLines = useMemo(() => hours.flatMap((h) => byHour.get(h)), [byHour, hours.join()]) // eslint-disable-line react-hooks/exhaustive-deps

  const piece = tape.piece
  const source = tape.inGap ? null : piece?.journal
    ? { label: 'A clip in place of the tapes (they have a gap here)', href: piece.url }
    : piece && { label: `NASA tape ${piece.tape}`, href: `https://archive.org/details/Apollo${mission.number}Audio` }

  const report = {
    missionName: mission.name,
    clipId: piece ? `the whole-mission recording (${piece.journal ? 'gap clip ' : 'NASA tape '}${piece.tape})` : 'the whole-mission recording',
    audioUrl: tape.url,
    sourceUrl: source?.href,
  }

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
          <button type="button" className="immersive-open" onClick={() => setImmersive(true)}>
            ⛶ Full-screen view
          </button>
          {source && (
            <a className="source-link" href={source.href} target="_blank" rel="noreferrer">
              {source.label} ↗
            </a>
          )}
        </div>
        <MissionPhaseDiagram phase={phase} mission={mission} />
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

      <label className="commentary-toggle">
        <input type="checkbox" checked={announcer} onChange={onAnnouncer} />
        Mission Control announcer
        <span>
          {announcer
            ? 'On: the public-affairs announcer ("This is Apollo Control…") plays, as it was broadcast.'
            : 'Off: his announcements are cut out. Where he talks over the crew he stays, as the two were recorded together.'}
        </span>
      </label>

      <label className="commentary-toggle">
        <input type="checkbox" checked={fill} onChange={(e) => onFill(e.target.checked)} />
        Fill gaps with clips
        <span>
          {fill
            ? "On: where NASA's tapes have no recording, a short clip of that moment plays in its place."
            : "Off: only NASA's tapes play."}
        </span>
      </label>

      {clips?.[clipIndex] && <MomentPhotos mission={mission} clip={{ ...clips[clipIndex], getSeconds: tape.get }} phase={phase} />}

      {immersive && (
        <ImmersiveView
          mission={mission}
          clips={clips}
          index={clipIndex}
          lines={shownLines}
          currentTime={tape.get}
          get={tape.get}
          phase={phase}
          onClose={closeImmersive}
          onLineSeek={(g) => tape.seek(g, true)}
          report={report}
          controls={
            <>
              <button type="button" className="immersive-skip" onClick={() => tape.seek(tape.get - 30)} aria-label="Back 30 seconds">
                −30
              </button>
              <button type="button" className="play-button" onClick={tape.toggle} aria-label={tape.playing ? 'Pause' : 'Play'}>
                {tape.loading && tape.playing ? '…' : tape.playing ? '❚❚' : '▶'}
              </button>
              <button type="button" className="immersive-skip" onClick={() => tape.seek(tape.get + 30)} aria-label="Forward 30 seconds">
                +30
              </button>
            </>
          }
        />
      )}

      {shownLines.length > 0 ? (
        <TranscriptPanel
          lines={shownLines}
          currentTime={tape.get}
          onTermClick={onTermClick}
          onLineSeek={(g) => tape.seek(g, true)}
          report={report}
          mission={mission.id}
          clip={hours.map(tapeClip).join(',')}
        />
      ) : (
        <p className="moment-description">No transcript for these hours of the mission.</p>
      )}
    </>
  )
}
