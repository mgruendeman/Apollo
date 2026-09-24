import { useCallback, useMemo, useState } from 'react'
import GlossaryText from './GlossaryText'
import SpeakerAvatar from './SpeakerAvatar'
import ReportDialog from './ReportDialog'
import { effectiveOffsets, activeLineIndex } from '../lib/transcriptTiming'
import { useTranscriptScroll } from '../lib/useTranscriptScroll'
import { useLongPress } from '../lib/useLongPress'
import { lineReport } from '../lib/lineReport'
import { REACTIONS, reactionsAvailable, useClipReactions } from '../lib/reactions'

const CHANNEL_TAGS = {
  onboard: 'onboard',
  pao: 'Mission Control',
}

const OVER_NOTE =
  "NASA's recordings are the broadcast mix: the announcer and the crew on one track. Where he talks over them, his voice can't be taken out, so he stays even with the announcer switched off."
const UNHEARD_NOTE =
  "NASA's transcript was typed from the full air-to-ground loop. This recording is the broadcast copy, which missed this call; it's shown so the conversation reads on."

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
export default function TranscriptPanel({ lines, currentTime, onTermClick, onLineSeek, report, mission, clip }) {
  const offsets = useMemo(() => effectiveOffsets(lines), [lines])
  const activeIndex = activeLineIndex(offsets, currentTime)

  // Scroll only the transcript box itself, never the page, so reading
  // elsewhere on the page isn't interrupted each time a new line starts.
  const { listRef, activeRef, away, jumpToCurrent, listProps } = useTranscriptScroll(activeIndex, lines)

  const [reporting, setReporting] = useState(null)
  const closeReport = useCallback(() => setReporting(null), [])
  const { bind, consumeClick } = useLongPress((i) => setReporting(i))
  const reactions = useClipReactions(mission, clip)
  const [picking, setPicking] = useState(null) // the line whose emoji picker is open

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
                className={['transcript-line', i === activeIndex && 'is-active', line.over && line.channel === 'pao' && 'is-over', line.unheard && 'is-unheard']
                  .filter(Boolean)
                  .join(' ')}
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
                  {line.over && (
                    <NoteTag label={line.channel === 'pao' ? 'talking over the crew' : 'announcer talking over'} note={OVER_NOTE} />
                  )}
                  {line.unheard && <NoteTag label="not on this recording" note={UNHEARD_NOTE} />}
                  <span className="transcript-get">{line.get}</span>
                  <span className="transcript-text">
                    <GlossaryText text={line.text} onTermClick={onTermClick} notes />
                  </span>
                  {reactionsAvailable && mission && clip && (
                    <Reactions
                      counts={reactions.get(line)}
                      open={picking === i}
                      onOpen={() => setPicking(picking === i ? null : i)}
                      onPick={(emoji) => {
                        reactions.toggle(line, emoji)
                        setPicking(null)
                      }}
                    />
                  )}
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

// A small tag on a line that explains itself when tapped (a tooltip
// wouldn't show on a phone).
function NoteTag({ label, note }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        className="transcript-channel-tag is-note"
        aria-expanded={open}
        onPointerDown={(e) => e.stopPropagation()}
        onClick={(e) => {
          e.stopPropagation()
          setOpen(!open)
        }}
      >
        {label} ⓘ
      </button>
      {open && <span className="transcript-note">{note}</span>}
    </>
  )
}

// A line's reaction counts, and a ☺ button that opens the five emojis.
function Reactions({ counts, open, onOpen, onPick }) {
  const stop = (fn) => (e) => {
    e.stopPropagation()
    fn()
  }
  const shown = REACTIONS.filter(([emoji]) => counts[emoji]?.n > 0)
  return (
    <span className="line-reactions" onPointerDown={(e) => e.stopPropagation()}>
      {shown.map(([emoji, label]) => (
        <button
          key={emoji}
          type="button"
          className={counts[emoji].mine ? 'reaction-chip is-mine' : 'reaction-chip'}
          aria-pressed={counts[emoji].mine}
          aria-label={`${label}: ${counts[emoji].n}`}
          onClick={stop(() => onPick(emoji))}
        >
          {emoji} {counts[emoji].n}
        </button>
      ))}
      <button type="button" className="reaction-add" aria-expanded={open} aria-label="React to this line" onClick={stop(onOpen)}>
        ☺<span aria-hidden="true">+</span>
      </button>
      {open && (
        <span className="reaction-picker" role="group" aria-label="Pick a reaction">
          {REACTIONS.map(([emoji, label]) => (
            <button key={emoji} type="button" title={label} aria-label={label} aria-pressed={!!counts[emoji]?.mine} onClick={stop(() => onPick(emoji))}>
              {emoji}
            </button>
          ))}
        </span>
      )}
    </span>
  )
}
