import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { glossary } from '../data/glossary'
import GlossaryText from '../components/GlossaryText'
import GlossaryPanel from '../components/GlossaryPanel'
import ReportIssueButton from '../components/ReportIssueButton'

// A dedicated deep-dive page for the handful of major-hardware/major-topic
// glossary entries that warrant more than the modal's short writeup — a
// fuller history, verified NASA/Wikimedia imagery, and room to breathe.
// Only entries flagged `deepDive: true` in glossary.js are reachable here;
// everything else stays a modal-only entry.
export default function GlossaryDetail() {
  const { id } = useParams()
  const [activeGlossaryEntry, setActiveGlossaryEntry] = useState(null)
  const entry = glossary.find((e) => e.id === id)

  if (!entry || !entry.deepDive) {
    return (
      <div className="page">
        <Link to="/glossary" className="back-link">
          ← Glossary
        </Link>
        <header className="mission-header">
          <p className="eyebrow">Reference</p>
          <h1>Not found</h1>
          <p className="lede">There's no deep-dive page for that entry.</p>
        </header>
      </div>
    )
  }

  return (
    <div className="page">
      <Link to="/glossary" className="back-link">
        ← Glossary
      </Link>

      <header className="mission-header">
        <p className="eyebrow">Deep dive</p>
        <h1>{entry.terms[0]}</h1>
        {entry.terms.length > 1 && (
          <p className="glossary-aliases">also: {entry.terms.slice(1).join(', ')}</p>
        )}
        <p className="lede">{entry.short}</p>
      </header>

      {entry.images && entry.images.length > 0 && (
        <section className="glossary-detail-images">
          {entry.images.map((img) => (
            <figure key={img.src} className="glossary-detail-figure">
              <img src={`${import.meta.env.BASE_URL}${img.src}`} alt={img.caption} loading="lazy" />
              <figcaption>
                <span>{img.caption}</span>
                <span className="glossary-detail-credit">
                  {img.credit}
                  {img.sourceUrl && (
                    <>
                      {' — '}
                      <a href={img.sourceUrl} target="_blank" rel="noreferrer">
                        source ↗
                      </a>
                    </>
                  )}
                </span>
              </figcaption>
            </figure>
          ))}
        </section>
      )}

      <section className="glossary-detail-body">
        {(entry.deepDiveText && entry.deepDiveText.length > 0
          ? entry.deepDiveText
          : [entry.long]
        ).map((paragraph, i) => (
          <p key={i}>
            <GlossaryText text={paragraph} onTermClick={setActiveGlossaryEntry} />
          </p>
        ))}
      </section>

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
        title={`Glossary: "${entry.terms[0]}" deep dive looks wrong`}
        body={`What's wrong with the "${entry.terms[0]}" deep-dive page?\n\n(current text)\n${(entry.deepDiveText || [entry.long]).join('\n\n')}`}
      >
        Report an inaccuracy
      </ReportIssueButton>

      <GlossaryPanel entry={activeGlossaryEntry} onClose={() => setActiveGlossaryEntry(null)} />
    </div>
  )
}
