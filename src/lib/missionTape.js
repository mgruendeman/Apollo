import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { MEDIA_URL } from '../config'

// Playback of a whole mission from NASA's tapes, by mission time (GET).
//
// public/timeline/apolloNN.json (pipeline/align_tapes.py) lists the pieces
// of tape in mission order: tape seconds `from`..`to` play mission time
// `get` + rate * (t - from). The recorders were stopped through quiet
// stretches, so between pieces there's no recording. Normally the player
// runs straight from one piece to the next; in real-time mode it counts
// through the gap at the true pace instead.
//
// Two <audio> elements take turns: while one plays, the other loads the
// next piece's tape and waits at its first second, so a change of tape
// doesn't stall.

export function tapeUrl(mission, tape, audio) {
  if (audio?.base) return `${audio.base.replace('{media}', MEDIA_URL)}/${tape}${audio.ext || '.mp3'}`
  return `https://archive.org/download/${audio?.item || `Apollo${Number(mission)}Audio`}/${tape}.mp3`
}

const endGet = (s) => s.get + (s.to - s.from) * s.rate

// The piece playing at mission time g, or the next one after it.
function pieceAt(segments, g) {
  let lo = 0
  let hi = segments.length - 1
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (endGet(segments[mid]) <= g) lo = mid + 1
    else hi = mid
  }
  return lo
}

export function useMissionTape(timeline, mission) {
  const segments = useMemo(() => timeline?.segments || [], [timeline])
  const audios = useRef([null, null])
  const active = useRef(0) // which of the two <audio> elements is playing
  const seg = useRef(0) // index of the piece playing (or the next, in a gap)
  const gapFrom = useRef(null) // real-time gap: [mission time at start, wall clock at start]
  const [get, setGet] = useState(segments[0]?.get ?? 0)
  const [playing, setPlaying] = useState(false)
  const [inGap, setInGap] = useState(false)
  const [loading, setLoading] = useState(false)
  const [realTime, setRealTime] = useState(false)
  const realTimeRef = useRef(false)
  realTimeRef.current = realTime

  const el = (i) => {
    if (!audios.current[i]) {
      const a = new Audio()
      a.preload = 'auto'
      audios.current[i] = a
    }
    return audios.current[i]
  }

  // Load piece k's tape into element i and put it at mission time g.
  const cueOn = useCallback(
    (i, k, g) => {
      const s = segments[k]
      const a = el(i)
      const url = s.url || tapeUrl(mission, s.tape, timeline.audio)
      const t = s.from + Math.max(0, g - s.get) / s.rate
      if (a.dataset.tape !== s.tape) {
        a.dataset.tape = s.tape
        a.src = url
      }
      if (a.readyState >= 1) a.currentTime = t
      else a.addEventListener('loadedmetadata', () => (a.currentTime = t), { once: true })
      return a
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [segments, mission, timeline],
  )

  const preloadNext = useCallback(
    (k) => {
      const next = segments[k + 1]
      if (!next) return
      const other = 1 - active.current
      if (next.tape === segments[k].tape) return // same tape: just keeps playing / seeks
      cueOn(other, k + 1, next.get)
    },
    [segments, cueOn],
  )

  // Start piece k at mission time g (inside it), on whichever element has it ready.
  const startPiece = useCallback(
    (k, g, play) => {
      const s = segments[k]
      const cur = el(active.current)
      let i = active.current
      if (cur.dataset.tape !== s.tape && el(1 - i).dataset.tape === s.tape) i = 1 - i
      if (i !== active.current) cur.pause()
      active.current = i
      seg.current = k
      gapFrom.current = null
      setInGap(false)
      const a = cueOn(i, k, g)
      if (play) {
        setLoading(true)
        a.play().catch(() => setPlaying(false))
      }
      preloadNext(k)
    },
    [segments, cueOn, preloadNext],
  )

  const seek = useCallback(
    (g, play = playing) => {
      if (!segments.length) return
      const k = pieceAt(segments, g)
      const s = segments[k]
      if (!play) {
        // just move there; the tape loads when play is pressed
        audios.current.forEach((a) => a?.pause())
        gapFrom.current = null
        seg.current = k
        setInGap(g < s.get)
        setGet(g)
        setPlaying(false)
        return
      }
      if (g >= s.get) return startPiece(k, g, play)
      // before piece k: a gap
      if (realTimeRef.current) {
        el(active.current).pause()
        seg.current = k
        gapFrom.current = [g, performance.now()]
        setPlaying(true)
        setInGap(true)
        setGet(g)
        cueOn(1 - active.current, k, s.get) // have the next piece ready
      } else {
        startPiece(k, s.get, play)
      }
    },
    [segments, playing, startPiece, cueOn],
  )

  // The pieces can change under the player (the journal-clip fill switched
  // on or off): pick up at the same mission time in the new set.
  const now = useRef({ get, playing })
  now.current = { get, playing }
  const firstSegments = useRef(true)
  useEffect(() => {
    if (firstSegments.current || !segments.length) {
      firstSegments.current = !segments.length
      return
    }
    seek(now.current.get, now.current.playing)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [segments])

  // At the end of piece k: on to the next, straight away or (in real time)
  // after counting through the gap.
  const advance = useCallback(
    (k) => {
      const s = segments[k]
      const a = el(active.current)
      const next = segments[k + 1]
      if (!next) {
        a.pause()
        return
      }
      if (realTimeRef.current && next.get > endGet(s) + 1) {
        gapFrom.current = [endGet(s), performance.now()]
        a.pause()
        seg.current = k + 1
        setInGap(true)
      } else if (next.tape === s.tape && Math.abs(next.from - s.to) < 0.5 && !a.ended) {
        seg.current = k + 1 // the next piece carries straight on in this tape
        preloadNext(k + 1)
      } else {
        startPiece(k + 1, next.get, true)
      }
    },
    [segments, startPiece, preloadNext],
  )
  const advanceRef = useRef(advance)
  advanceRef.current = advance
  const segsRef = useRef(segments)
  segsRef.current = segments

  // The clock: follow the playing tape, hand over at the end of each piece.
  useEffect(() => {
    let raf = 0
    const tick = () => {
      raf = requestAnimationFrame(tick)
      const k = seg.current
      const s = segments[k]
      if (!s) return
      if (gapFrom.current) {
        const g = gapFrom.current[0] + (performance.now() - gapFrom.current[1]) / 1000
        if (g >= s.get) startPiece(k, s.get, true)
        else setGet(g)
        return
      }
      const a = el(active.current)
      if (a.paused || a.dataset.tape !== s.tape) return
      const t = a.currentTime
      if (t < s.from - 1) return // still seeking into the piece
      setGet(s.get + (t - s.from) * s.rate)
      // (a tape file can end a moment before the piece's measured end)
      if (t >= Math.min(s.to, a.duration || Infinity) - 0.05) advance(k)
    }
    if (playing) raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [playing, segments, startPiece, advance])

  // Keep React's playing/loading state in step with the elements.
  useEffect(() => {
    const on = (a) => {
      const handlers = {
        playing: () => {
          setPlaying(true)
          setLoading(false)
        },
        waiting: () => setLoading(true),
        pause: () => {
          if (a === el(active.current) && !gapFrom.current && !a.ended) setPlaying(false)
        },
        ended: () => {
          const s = segsRef.current[seg.current]
          if (a === el(active.current) && s && a.dataset.tape === s.tape) advanceRef.current(seg.current)
        },
      }
      Object.entries(handlers).forEach(([e, f]) => a.addEventListener(e, f))
      return () => Object.entries(handlers).forEach(([e, f]) => a.removeEventListener(e, f))
    }
    const offs = [on(el(0)), on(el(1))]
    const els = audios.current
    return () => {
      offs.forEach((f) => f())
      els.forEach((a) => a?.pause())
    }
  }, [])

  const pause = useCallback(() => {
    audios.current.forEach((a) => a?.pause())
    gapFrom.current = null
    setPlaying(false)
  }, [])

  const toggle = useCallback(() => {
    if (playing) pause()
    else seek(get, true)
  }, [playing, get, seek, pause])

  return {
    get,
    playing,
    loading,
    inGap,
    realTime,
    setRealTime,
    seek,
    toggle,
    pause,
    segments,
    piece: segments[seg.current],
  }
}

// The journal's clips fill what the tapes don't cover: every stretch of a
// clip outside the tape pieces (and outside clips already used) becomes a
// piece of its own, so the mission plays on through the tapes' gaps.
export function withJournalFill(timeline, clips) {
  if (!timeline || !clips) return timeline
  const covered = timeline.segments.map((s) => [s.get, endGet(s)])
  const pieces = []
  for (const c of [...clips].sort((a, b) => a.getSeconds - b.getSeconds)) {
    if (!c.durationSeconds || !c.audioUrl) continue
    let parts = [[c.getSeconds, c.getSeconds + c.durationSeconds]]
    for (const [a, b] of covered) {
      if (b <= parts[0]?.[0] || a >= parts[parts.length - 1]?.[1]) continue
      parts = parts.flatMap(([x, y]) => (b <= x || a >= y ? [[x, y]] : [[x, a], [b, y]].filter(([p, q]) => q - p > 0)))
    }
    for (const [x, y] of parts) {
      if (y - x < 8) continue
      pieces.push({ tape: c.id, url: c.audioUrl, from: x - c.getSeconds, to: y - c.getSeconds, get: x, rate: 1, journal: true })
      covered.push([x, y])
    }
  }
  return { ...timeline, segments: [...timeline.segments, ...pieces].sort((a, b) => a.get - b.get) }
}

export function formatGetSigned(g) {
  const sign = g < 0 ? '-' : ''
  const t = Math.floor(Math.abs(g))
  return `${sign}${String(Math.floor(t / 3600)).padStart(3, '0')}:${String(Math.floor((t % 3600) / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`
}
