import { useEffect, useMemo, useRef } from 'react'
import GlossaryText from './GlossaryText'
import SpeakerAvatar from './SpeakerAvatar'
import { effectiveOffsets, activeLineIndex } from '../lib/transcriptTiming'

const CHANNEL_TAGS = {
  onboard: 'onboard',
  pao: 'Mission Control',
}

// How long a manual scroll of the transcript box pauses auto-scrolling.
const USER_SCROLL_HOLD_MS = 6000

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
  const userScrolledAt = useRef(0)

  const offsets = useMemo(() => effectiveOffsets(lines), [lines])

  const activeIndex = activeLineIndex(offsets, currentTime)

  // Scroll only the transcript box itself, never the page, so reading
  // elsewhere on the page isn't interrupted each time a new line starts.
  useEffect(() => {
    const list = listRef.current
    const line = activeLineRef.current
    if (!list || !line) return
    if (Date.now() - userScrolledAt.current < USER_SCROLL_HOLD_MS) return
    list.scrollTo({
      top: line.offsetTop - list.clientHeight / 2 + line.clientHeight / 2,
      behavior: 'smooth',
    })
  }, [activeIndex])

  function markUserScroll() {
    userScrolledAt.current = Date.now()
  }

  if (lines.length === 0) {
    return null
  }

  return (
    <div className="transcript-panel">
      <p className="glossary-hint">
        Dotted-underline words are clickable for more · click a line to jump
        there
      </p>
      <div
        className="transcript-list"
        ref={listRef}
        onWheel={markUserScroll}
        onTouchMove={markUserScroll}
      >
        {lines.map((line, i) => {
          return (
            <div
              key={`${line.get}-${i}`}
              ref={i === activeIndex ? activeLineRef : null}
              className={i === activeIndex ? 'transcript-line is-active' : 'transcript-line'}
              onClick={() => onLineSeek?.(offsets[i])}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onLineSeek?.(offsets[i])
              }}
            >
              <SpeakerAvatar name={line.speaker} />
              <span className="transcript-body">
                <span className="transcript-speaker">{line.speaker}</span>
                {CHANNEL_TAGS[line.channel] && (
                  <span className="transcript-channel-tag">{CHANNEL_TAGS[line.channel]}</span>
                )}
                <span className="transcript-get">{line.get}</span>
                <span className="transcript-text">
                  <GlossaryText text={line.text} onTermClick={onTermClick} notes />
                </span>
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
