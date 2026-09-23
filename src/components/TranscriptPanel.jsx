import { useCallback, useMemo, useState } from 'react'
import GlossaryText from './GlossaryText'
import SpeakerAvatar from './SpeakerAvatar'
import ReportDialog from './ReportDialog'
import { effectiveOffsets, activeLineIndex } from '../lib/transcriptTiming'
import { useTranscriptScroll } from '../lib/useTranscriptScroll'
import { useLongPress } from '../lib/useLongPress'
import { lineReport } from '../lib/lineReport'

const CHANNEL_TAGS = {
  onboard: 'onboard',
  pao: 'Mission Control',
}

// Keyed by moment.id from the parent, so switching clips mounts a fresh
// instance instead of needing an effect to reset scroll position.
//
// All channels (air-to-ground, onboard, PAO) are shown together in one
// chronological stream — they're all the same single recording anyway, so
// splitting them into separate filtered views just made it harder to
// follow the conversation. A small tag marks anything that wasn't a
// transmitted radio call.
//
// Press and hold a line (or right-click it) to report a problem with it.
export default function TranscriptPanel({ lines, currentTime, onTermClick, onLineSeek, report }) {
  const offsets = useMemo(() => effectiveOffsets(lines), [lines])
  const activeIndex = activeLineIndex(offsets, currentTime)

  // Scroll only the transcript box itself, never the page, so reading
  // elsewhere on the page isn't interrupted each time a new line starts.
  const { listRef, activeRef, away, jumpToCurrent, listProps } = useTranscriptScroll(activeIndex, lines)

  const [reporting, setReporting] = useState(null)
  const closeReport = useCallback(() => setReporting(null), [])
  const { bind, consumeClick } = useLongPress((i) => setReporting(i))

  if (lines.length === 0) {
    return null
  }

  const reportDetails = reporting !== null && report ? lineReport(report, lines[reporting], offsets[reporting]) : null

  return (
    <div className="transcript-panel">
      <p className="glossary-hint">
        Dotted-underline words and ⓘ explain more · click a line to jump there · press and hold a line to report a
        problem
      </p>
      <div className="transcript-frame">
        <div className="transcript-list" ref={listRef} {...listProps}>
          {lines.map((line, i) => {
            return (
              <div
                key={`${line.get}-${i}`}
                ref={i === activeIndex ? activeRef : null}
                className={i === activeIndex ? 'transcript-line is-active' : 'transcript-line'}
                onClick={() => {
                  if (!consumeClick()) onLineSeek?.(offsets[i])
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) onLineSeek?.(offsets[i])
                }}
                {...bind(i)}
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
        {away && activeIndex >= 0 && (
          <button type="button" className="jump-current" onClick={jumpToCurrent}>
            Current line ↧
          </button>
        )}
      </div>
      {reportDetails && <ReportDialog title={reportDetails.title} context={reportDetails.context} onClose={closeReport} />}
    </div>
  )
}
