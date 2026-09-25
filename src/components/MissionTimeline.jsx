import { useMemo } from 'react'
import { classifyEventType, EVENT_TYPE_META } from '../data/eventType'
import { buildChapters } from '../lib/missionIndex'
import { photosByClipId } from '../data/photos'
import { PHASES } from '../data/phases'
import PhaseIcon from './PhaseIcon'

// A chapter's kind, for its icon: the flight's big moments (launch, the
// landing, leaving the Moon, splashdown) and chapters holding one of the
// mission's highlights are milestones; one whose lines are largely about
// sleep is a rest.
const MILESTONE_PHASES = new Set(['launch', 'landing', 'ascent', 'splashdown'])
function chapterType(ch, chapterClips, highlightIds, previewFor) {
  if (MILESTONE_PHASES.has(ch.phase) || chapterClips.some((c) => highlightIds.has(c.id))) return 'major'
  const kinds = chapterClips.map((c) => classifyEventType(previewFor(c) || ''))
  if (kinds.filter((k) => k === 'rest').length * 3 >= kinds.length) return 'rest'
  return 'routine'
}

export default function MissionTimeline({ mission, clips, transcripts, phases, activeIndex, onSelect }) {
  const chapters = useMemo(() => buildChapters(clips, phases), [clips, phases])
  const highlightIds = new Set((mission.highlights || []).map((h) => h.id))
  const activeChapterIndex = chapters.findIndex(
    (ch) => activeIndex >= ch.startIndex && activeIndex < ch.endIndex,
  )

  function previewFor(c) {
    const lines = transcripts?.[c.id]
    if (lines && lines.length) return `${lines[0].speaker}: ${lines[0].text}`
    return null
  }

  // A chapter that happens to contain one of the mission's curated
  // highlight clips gets that highlight's opening line shown as a
  // pull-quote, so the timeline surfaces its "big moments" at a glance
  // instead of requiring every chapter to be opened to find them.
  function highlightFor(ch) {
    if (!mission.highlights) return null
    const hit = mission.highlights.find((h) => {
      const idx = clips.findIndex((c) => c.id === h.id)
      return idx >= ch.startIndex && idx < ch.endIndex
    })
    if (!hit) return null
    const lines = transcripts?.[hit.id]
    return { title: hit.title, quote: lines?.[0]?.text }
  }

  return (
    <section className="timeline">
      <h3>Full mission timeline</h3>
      <p className="timeline-legend">
        <span className="legend-item">★ major milestone</span>
        <span className="legend-item">☾ rest / routine period</span>
      </p>
      <p className="timeline-legend timeline-phases">
        {Object.keys(PHASES).map((ph) => (
          <span key={ph} className="legend-item">
            <PhaseIcon phase={ph} /> {PHASES[ph].label}
          </span>
        ))}
      </p>
      {chapters.map((ch, ci) => {
        const count = ch.endIndex - ch.startIndex
        const chapterClips = clips.slice(ch.startIndex, ch.endIndex)
        const eventType = chapterType(ch, chapterClips, highlightIds, previewFor)
        const meta = EVENT_TYPE_META[eventType]
        const highlight = highlightFor(ch)
        const types = chapterClips.map((c) =>
          highlightIds.has(c.id)
            ? 'major'
            : classifyEventType(previewFor(c) || ''),
        )

        return (
          <details key={ch.startIndex} open={ci === activeChapterIndex} className={meta.className}>
            <summary>
              <span className="chapter-phase">
                <PhaseIcon phase={ch.phase} />
              </span>
              <span className="chapter-get">
                <span>{chapterClips[0].get}</span>
                {count > 1 && chapterClips[count - 1].get !== chapterClips[0].get && (
                  <span className="chapter-get-end">to {chapterClips[count - 1].get}</span>
                )}
              </span>
              <span className="chapter-label">
                {meta.icon && <span className="chapter-icon">{meta.icon} </span>}
                {ch.title}
              </span>
              <span className="chapter-count">
                {count} clip{count === 1 ? '' : 's'}
              </span>
            </summary>
            {highlight && (
              <blockquote className="chapter-quote">
                <p className="chapter-quote-title">{highlight.title}</p>
                {highlight.quote && <p>&ldquo;{highlight.quote}&rdquo;</p>}
              </blockquote>
            )}
            <ol>
              {chapterClips.map((c, k) => {
                // Routine exchanges stay in the list, as compact rows, so
                // nothing is hidden and the milestones still stand out.
                const i = ch.startIndex + k
                return (
                  <TimelineClipRow
                    key={c.id}
                    clip={c}
                    type={types[k]}
                    preview={previewFor(c)}
                    chapterLabel={ch.title}
                    isActive={i === activeIndex}
                    onSelect={() => onSelect(i)}
                  />
                )
              })}
            </ol>
          </details>
        )
      })}
    </section>
  )
}

function TimelineClipRow({ clip, type, preview, chapterLabel, isActive, onSelect }) {
  const meta = EVENT_TYPE_META[type]
  const photo = photosByClipId[clip.id]
  return (
    <li>
      <button
        type="button"
        className={['moment-item', isActive && 'is-active', type === 'routine' && 'is-routine'].filter(Boolean).join(' ')}
        onClick={onSelect}
      >
        <span className="moment-get">{clip.get}</span>
        {meta.icon && <span className="moment-icon">{meta.icon}</span>}
        <span className="moment-title">
          {(preview || chapterLabel).slice(0, type === 'routine' ? 70 : 100)}
        </span>
        {photo && (
          <img
            className="moment-thumb"
            src={`${import.meta.env.BASE_URL}${photo.src}`}
            alt=""
            loading="lazy"
          />
        )}
      </button>
    </li>
  )
}
