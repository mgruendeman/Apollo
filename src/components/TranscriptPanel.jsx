import { useEffect, useMemo, useRef, useState } from 'react'

function firstChannel(lines) {
  const set = new Set(lines.map((l) => l.channel))
  return ['air-to-ground', 'onboard', 'pao'].find((c) => set.has(c)) || 'air-to-ground'
}

const CHANNEL_LABELS = {
  'air-to-ground': 'Air-to-Ground',
  onboard: 'Onboard',
  pao: 'Mission Control',
}

function speakerColor(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 55%, 42%)`
}

function initials(name) {
  const words = name.trim().split(/\s+/)
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[words.length - 1][0]).toUpperCase()
}

// Keyed by moment.id from the parent, so switching clips mounts a fresh
// instance with the right default channel instead of needing an effect to
// reset it.
export default function TranscriptPanel({ lines, currentTime }) {
  const [channel, setChannel] = useState(() => firstChannel(lines))
  const listRef = useRef(null)
  const activeLineRef = useRef(null)

  const channelsPresent = useMemo(() => {
    const set = new Set(lines.map((l) => l.channel))
    return ['air-to-ground', 'onboard', 'pao'].filter((c) => set.has(c))
  }, [lines])

  const filtered = useMemo(
    () => lines.filter((l) => l.channel === channel),
    [lines, channel],
  )

  const activeIndex = useMemo(() => {
    let idx = -1
    for (let i = 0; i < filtered.length; i++) {
      if (filtered[i].offsetSeconds <= currentTime) idx = i
      else break
    }
    return idx
  }, [filtered, currentTime])

  useEffect(() => {
    activeLineRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [activeIndex])

  if (lines.length === 0) {
    return null
  }

  return (
    <div className="transcript-panel">
      {channelsPresent.length > 1 && (
        <div className="channel-toggle">
          {channelsPresent.map((c) => (
            <button
              key={c}
              type="button"
              className={c === channel ? 'channel-chip is-active' : 'channel-chip'}
              onClick={() => setChannel(c)}
            >
              {CHANNEL_LABELS[c]}
            </button>
          ))}
        </div>
      )}
      <div className="transcript-list" ref={listRef}>
        {filtered.map((line, i) => (
          <div
            key={`${line.get}-${i}`}
            ref={i === activeIndex ? activeLineRef : null}
            className={i === activeIndex ? 'transcript-line is-active' : 'transcript-line'}
          >
            <span
              className="speaker-badge"
              style={{ background: speakerColor(line.speaker) }}
              title={line.speaker}
            >
              {initials(line.speaker)}
            </span>
            <span className="transcript-body">
              <span className="transcript-speaker">{line.speaker}</span>
              <span className="transcript-get">{line.get}</span>
              <span className="transcript-text">{line.text}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
