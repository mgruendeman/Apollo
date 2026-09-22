import { useEffect, useMemo, useRef } from 'react'
import GlossaryText from './GlossaryText'
import { speakerAvatar } from '../data/speakers'

const CHANNEL_TAGS = {
  onboard: 'onboard',
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
// instance instead of needing an effect to reset scroll position.
//
// All channels (air-to-ground, onboard, PAO) are shown together in one
// chronological stream — they're all the same single recording anyway, so
// splitting them into separate filtered views just made it harder to
// follow the conversation. A small tag marks anything that wasn't a
// transmitted radio call.
export default function TranscriptPanel({ lines, currentTime, onTermClick, onLineSeek }) {
  const listRef = useRef(null)
  const activeLineRef = useRef(null)

  const activeIndex = useMemo(() => {
    let idx = -1
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].offsetSeconds <= currentTime) idx = i
      else break
    }
    return idx
  }, [lines, currentTime])

  useEffect(() => {
    activeLineRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [activeIndex])

  if (lines.length === 0) {
    return null
  }

  return (
    <div className="transcript-panel">
      <p className="glossary-hint">
        Dotted-underline words are clickable for more · click a line to jump
        there
      </p>
      <div className="transcript-list" ref={listRef}>
        {lines.map((line, i) => {
          const avatar = speakerAvatar(line.speaker)
          return (
            <div
              key={`${line.get}-${i}`}
              ref={i === activeIndex ? activeLineRef : null}
              className={i === activeIndex ? 'transcript-line is-active' : 'transcript-line'}
              onClick={() => onLineSeek?.(line.offsetSeconds)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onLineSeek?.(line.offsetSeconds)
              }}
            >
              {avatar ? (
                <img className="speaker-avatar" src={avatar} alt={line.speaker} title={line.speaker} />
              ) : (
                <span
                  className="speaker-badge"
                  style={{ background: speakerColor(line.speaker) }}
                  title={line.speaker}
                >
                  {initials(line.speaker)}
                </span>
              )}
              <span className="transcript-body">
                <span className="transcript-speaker">{line.speaker}</span>
                {CHANNEL_TAGS[line.channel] && (
                  <span className="transcript-channel-tag">{CHANNEL_TAGS[line.channel]}</span>
                )}
                <span className="transcript-get">{line.get}</span>
                <span className="transcript-text">
                  <GlossaryText text={line.text} onTermClick={onTermClick} />
                </span>
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
