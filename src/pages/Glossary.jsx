import { useState } from 'react'
import { Link } from 'react-router-dom'
import { glossary } from '../data/glossary'
import GlossaryText from '../components/GlossaryText'
import GlossaryPanel from '../components/GlossaryPanel'
import ReportIssueButton from '../components/ReportIssueButton'

// A full listing of every glossary entry in one place — mainly so the
// definitions can actually be read end-to-end and proofread, rather than
// only ever being discovered one at a time by clicking a term buried in a
// transcript somewhere.
export default function Glossary() {
  const [activeGlossaryEntry, setActiveGlossaryEntry] = useState(null)

  return (
    <div className="page">
      <Link to="/" className="back-link">
        ← All missions
      </Link>

      <header className="mission-header">
        <p className="eyebrow">Reference</p>
        <h1>Glossary</h1>
        <p className="lede">
          Every term that's clickable in a transcript, all in one place —
          jargon, hardware, roles, and procedures that come up across the
          missions.
        </p>
      </header>

      <section className="glossary-index">
        {glossary.map((entry) => (
          <article key={entry.id} className="glossary-entry" id={entry.id}>
            <h3>{entry.terms[0]}</h3>
            {entry.terms.length > 1 && (
              <p className="glossary-aliases">also: {entry.terms.slice(1).join(', ')}</p>
            )}
            <p className="glossary-long">
              <GlossaryText text={entry.long} onTermClick={setActiveGlossaryEntry} excludeId={entry.id} />
            </p>
            {entry.bullets && (
              <ul className="glossary-bullets">
                {entry.bullets.map((item) => (
                  <li key={item}>
                    <GlossaryText text={item} onTermClick={setActiveGlossaryEntry} excludeId={entry.id} />
                  </li>
                ))}
              </ul>
            )}
            {entry.deepDive && (
              <Link to={`/glossary/${entry.id}`} className="glossary-read-more">
                Read the deep dive, with photos &amp; diagrams →
              </Link>
            )}
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
              Report an inaccuracy
            </ReportIssueButton>
          </article>
        ))}
      </section>

      <GlossaryPanel
        entry={activeGlossaryEntry}
        onClose={() => setActiveGlossaryEntry(null)}
        onTermClick={setActiveGlossaryEntry}
      />
    </div>
  )
}
