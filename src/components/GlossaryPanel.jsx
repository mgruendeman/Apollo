import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import ReportIssueButton from './ReportIssueButton'
import GlossaryAbbr from './GlossaryAbbr'
import { hasDetailPage } from '../data/glossary'
import GlossaryText from './GlossaryText'

export default function GlossaryPanel({ entry, onClose, onTermClick }) {
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
        {entry.isNote && <p className="glossary-note-eyebrow">What this means</p>}
        <h3>{entry.terms[0]}</h3>
        {entry.terms.length > 1 && (
          <p className="glossary-aliases">
            also: {entry.terms.slice(1).join(', ')}
          </p>
        )}
        <GlossaryAbbr entry={entry} />
        <p className="glossary-long">
          <GlossaryText text={entry.long} onTermClick={onTermClick} excludeId={entry.id} />
        </p>
        {entry.bullets && (
          <ul className="glossary-bullets">
            {entry.bullets.map((b) => (
              <li key={b}>
                <GlossaryText text={b} onTermClick={onTermClick} excludeId={entry.id} />
              </li>
            ))}
          </ul>
        )}
        {hasDetailPage(entry) && (
          <Link to={`/glossary/${entry.id}`} className="glossary-read-more" onClick={onClose}>
            {entry.deepDive ? 'Read the deep dive, with photos & diagrams →' : 'Read more, with a quote from the mission →'}
          </Link>
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
          title={entry.isNote ? `Explanation of "${entry.terms[0]}" looks wrong` : `Glossary: "${entry.terms[0]}" looks wrong`}
          body={`What's wrong with the "${entry.terms[0]}" glossary entry?\n\n(current text)\n${entry.long}`}
        >
          Report an inaccuracy in this entry
        </ReportIssueButton>
      </div>
    </div>
  )
}
