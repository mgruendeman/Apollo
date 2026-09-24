import { useMemo, useState } from 'react'
import { classifyEventType, EVENT_TYPE_META } from '../data/eventType'
import { stripSourcePrefix } from '../lib/sourceLabel'
import { photosByClipId } from '../data/photos'
import { PHASES } from '../data/phases'
import PhaseIcon from './PhaseIcon'

// Collapse a run of this many or more back-to-back routine clips into a
// single expandable row, so a quiet multi-hour stretch doesn't bury the
// milestones around it in dozens of near-identical rows.
const COLLAPSE_THRESHOLD = 5

// The archive's own page labels ("Day 1, part 1" / "part 2" / ...) aren't
// strictly time-ordered — pages overlap and a handful of clips from an
// earlier or later page get interleaved by GET — so grouping on an exact
// label match fragments the timeline into dozens of alternating slivers.
// Instead we track each label's first-seen order and only open a new
// chapter when we reach a *later* label than the current one; anything
// that would be a step backward gets folded into the chapter already in
// progress. Index ranges stay contiguous, so callers can keep slicing
// `clips` by startIndex/endIndex as before.
function buildChapters(clips) {
  const order = new Map()
  for (const c of clips) {
    if (!order.has(c.sourceLabel)) order.set(c.sourceLabel, order.size)
  }

  const chapters = []
  for (let i = 0; i < clips.length; i++) {
    const label = clips[i].sourceLabel
    const rank = order.get(label)
    const current = chapters[chapters.length - 1]
    if (current && rank <= current.rank) {
      current.endIndex = i + 1
    } else {
      chapters.push({ label, rank, startIndex: i, endIndex: i + 1 })
    }
  }
  return chapters
}

function buildRows(types) {
  const rows = []
  let i = 0
  while (i < types.length) {
    if (types[i] === 'routine') {
      let j = i
      while (j < types.length && types[j] === 'routine') j++
      if (j - i >= COLLAPSE_THRESHOLD) {
        rows.push({ kind: 'run', start: i, end: j })
        i = j
        continue
      }
    }
    rows.push({ kind: 'clip', index: i })
    i++
  }
  return rows
}

// Brief events that name a chapter even when most of its clips are before
// or after them: a chapter that includes the landing is the descent.
const EVENT_PHASES = ['launch', 'landing', 'ascent', 'splashdown']

// The phase a chapter is about, for its icon: a key event among its own
// clips, or else the phase most of them are in. Only the chapter's own page
// counts: a chapter also holds the other journal's clips from the same hours
// (Surface Journal pages take in the Flight Journal's CSM-only clips), which
// would otherwise swing a surface chapter's icon to lunar orbit.
function chapterPhase(phases, clips, start, end, label) {
  const counts = {}
  for (let i = start; i < end; i++) {
    if (phases?.[i] && clips[i].sourceLabel === label) counts[phases[i]] = (counts[phases[i]] || 0) + 1
  }
  const event = EVENT_PHASES.find((p) => counts[p])
  return event || Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0]
}

export default function MissionTimeline({ mission, clips, transcripts, phases, activeIndex, onSelect }) {
  const [expandedRuns, setExpandedRuns] = useState(() => new Set())

  const chapters = useMemo(() => buildChapters(clips), [clips])
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

  function toggleRun(key) {
    setExpandedRuns((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
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
        const eventType = classifyEventType(ch.label)
        const meta = EVENT_TYPE_META[eventType]
        const highlight = highlightFor(ch)
        const chapterClips = clips.slice(ch.startIndex, ch.endIndex)
        const types = chapterClips.map((c) =>
          highlightIds.has(c.id)
            ? 'major'
            : classifyEventType(`${c.sourceLabel} ${previewFor(c) || ''}`),
        )
        const rows = buildRows(types)

        return (
          <details key={ch.startIndex} open={ci === activeChapterIndex} className={meta.className}>
            <summary>
              <span className="chapter-phase">
                <PhaseIcon phase={chapterPhase(phases, clips, ch.startIndex, ch.endIndex, ch.label)} />
              </span>
              <span className="chapter-get">
                <span>{chapterClips[0].get}</span>
                {count > 1 && chapterClips[count - 1].get !== chapterClips[0].get && (
                  <span className="chapter-get-end">to {chapterClips[count - 1].get}</span>
                )}
              </span>
              <span className="chapter-label">
                {meta.icon && <span className="chapter-icon">{meta.icon} </span>}
                {stripSourcePrefix(ch.label)}
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
              {rows.map((row) => {
                if (row.kind === 'run') {
                  const key = `${ch.startIndex}-${row.start}`
                  const expanded = expandedRuns.has(key)
                  const first = chapterClips[row.start]
                  const last = chapterClips[row.end - 1]
                  if (!expanded) {
                    return (
                      <li key={key}>
                        <button
                          type="button"
                          className="timeline-run-toggle"
                          onClick={() => toggleRun(key)}
                        >
                          <span className="moment-get">
                            {first.get}–{last.get}
                          </span>
                          <span className="moment-title">
                            {row.end - row.start} routine exchanges — click to expand
                          </span>
                        </button>
                      </li>
                    )
                  }
                  return chapterClips.slice(row.start, row.end).map((c, k) => {
                    const i = ch.startIndex + row.start + k
                    return (
                      <TimelineClipRow
                        key={c.id}
                        clip={c}
                        type={types[row.start + k]}
                        preview={previewFor(c)}
                        chapterLabel={ch.label}
                        isActive={i === activeIndex}
                        onSelect={() => onSelect(i)}
                      />
                    )
                  })
                }

                const c = chapterClips[row.index]
                const i = ch.startIndex + row.index
                return (
                  <TimelineClipRow
                    key={c.id}
                    clip={c}
                    type={types[row.index]}
                    preview={previewFor(c)}
                    chapterLabel={ch.label}
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
        className={isActive ? 'moment-item is-active' : 'moment-item'}
        onClick={onSelect}
      >
        <span className="moment-get">{clip.get}</span>
        {meta.icon && <span className="moment-icon">{meta.icon}</span>}
        <span className="moment-title">
          {(preview || stripSourcePrefix(chapterLabel)).slice(0, 100)}
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
