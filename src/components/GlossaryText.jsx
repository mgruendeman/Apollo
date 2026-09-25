import { glossaryMatchRegex, findGlossaryEntry } from '../data/glossary'
import { findInfoNotes } from '../data/infoNotes'

// Splits text on glossary terms and wraps the first match of each in a clickable span,
// so any transcript line (or description) can offer a rabbit hole into the
// glossary without every caller re-implementing the regex split.
// `excludeId` leaves an entry's own terms as plain text inside its own card.
// With `notes`, numbers and jargon the glossary doesn't cover ("170 by
// 61.8", "5 plus 52", "P63"...) get a small ⓘ that opens an explanation in
// the same panel.
export default function GlossaryText({ text, onTermClick, excludeId, notes = false }) {
  let key = 0
  // Each entry is underlined once per text: its first mention. (A long line
  // naming the terminator three times shouldn't be three links.)
  const linked = new Set()

  function glossaryParts(chunk) {
    // A fresh RegExp per call (not the shared module instance) so this
    // component never mutates lastIndex on state outside its own scope.
    const re = new RegExp(glossaryMatchRegex.source, glossaryMatchRegex.flags)
    const parts = []
    let lastIndex = 0
    let match
    while ((match = re.exec(chunk))) {
      if (match.index > lastIndex) {
        parts.push(chunk.slice(lastIndex, match.index))
      }
      const entry = findGlossaryEntry(match[0])
      if (entry && entry.id !== excludeId && onTermClick && !linked.has(entry.id)) {
        linked.add(entry.id)
        parts.push(
          <button
            key={key++}
            type="button"
            className="glossary-term"
            onClick={(e) => {
              e.stopPropagation()
              onTermClick(entry)
            }}
          >
            {match[0]}
          </button>,
        )
      } else {
        parts.push(match[0])
      }
      lastIndex = match.index + match[0].length
    }
    if (lastIndex < chunk.length) {
      parts.push(chunk.slice(lastIndex))
    }
    return parts
  }

  if (!notes || !onTermClick) return <>{glossaryParts(text)}</>

  const parts = []
  let pos = 0
  for (const f of findInfoNotes(text)) {
    parts.push(...glossaryParts(text.slice(pos, f.start)))
    parts.push(
      <span key={key++} className="info-note">
        {text.slice(f.start, f.end)}
        <button
          type="button"
          className="info-dot"
          aria-label={`What does "${f.note.title}" mean?`}
          onClick={(e) => {
            e.stopPropagation()
            onTermClick({ id: `note-${f.note.title}`, terms: [f.note.title], long: f.note.text, isNote: true })
          }}
        >
          i
        </button>
      </span>,
    )
    pos = f.end
  }
  parts.push(...glossaryParts(text.slice(pos)))
  return <>{parts}</>
}
