import { glossaryMatchRegex, findGlossaryEntry } from '../data/glossary'

// Splits text on glossary terms and wraps each match in a clickable span,
// so any transcript line (or description) can offer a rabbit hole into the
// glossary without every caller re-implementing the regex split.
export default function GlossaryText({ text, onTermClick }) {
  // A fresh RegExp per call (not the shared module instance) so this
  // component never mutates lastIndex on state outside its own scope.
  const re = new RegExp(glossaryMatchRegex.source, glossaryMatchRegex.flags)
  const parts = []
  let lastIndex = 0
  let match
  let key = 0

  while ((match = re.exec(text))) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    const entry = findGlossaryEntry(match[0])
    if (entry) {
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
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }
  return <>{parts}</>
}
