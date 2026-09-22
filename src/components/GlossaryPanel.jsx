import { useEffect } from 'react'
import ReportIssueButton from './ReportIssueButton'

export default function GlossaryPanel({ entry, onClose }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!entry) return null

  return (
    <div className="glossary-overlay" onClick={onClose} role="presentation">
      <div
        className="glossary-panel"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <button type="button" className="glossary-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h3>{entry.terms[0]}</h3>
        {entry.terms.length > 1 && (
          <p className="glossary-aliases">
            also: {entry.terms.slice(1).join(', ')}
          </p>
        )}
        <p className="glossary-long">{entry.long}</p>
        {entry.quote && (
          <blockquote className="glossary-quote">
            <p>{entry.quote.text}</p>
            <cite>— {entry.quote.attribution}</cite>
          </blockquote>
        )}
        {entry.links && entry.links.length > 0 && (
          <div className="glossary-links">
            {entry.links.map((l) => (
              <a key={l.url} href={l.url} target="_blank" rel="noreferrer">
                {l.label} ↗
              </a>
            ))}
          </div>
        )}
        <ReportIssueButton
          title={`Glossary: "${entry.terms[0]}" looks wrong`}
          body={`What's wrong with the "${entry.terms[0]}" glossary entry?\n\n(current text)\n${entry.long}`}
        >
          Report an inaccuracy in this entry
        </ReportIssueButton>
      </div>
    </div>
  )
}
