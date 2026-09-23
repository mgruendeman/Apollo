import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { glossary, hasDetailPage } from '../data/glossary'
import GlossaryText from '../components/GlossaryText'
import GlossaryPanel from '../components/GlossaryPanel'
import ReportIssueButton from '../components/ReportIssueButton'
import GlossaryAbbr from '../components/GlossaryAbbr'

// A full listing of every glossary entry in one place — mainly so the
// definitions can actually be read end-to-end and proofread, rather than
// only ever being discovered one at a time by clicking a term buried in a
// transcript somewhere.
// Everything a reader might search for in an entry.
function searchText(entry) {
  return [
    ...entry.terms,
    ...(entry.abbr || []).flatMap((a) => [a.short, a.full]),
    entry.short,
    entry.long,
    ...(entry.bullets || []),
  ]
    .join(' ')
    .toLowerCase()
}

export default function Glossary() {
  const [activeGlossaryEntry, setActiveGlossaryEntry] = useState(null)
  // Kept in the address (#/glossary?q=...) so a search can be shared.
  const [params, setParams] = useSearchParams()
  const query = params.get('q') || ''

  const results = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean)
    if (!words.length) return glossary
    const esc = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    // Whole words first ("seco" shouldn't find every "second"), then words
    // starting with the query, then anywhere.
    const tiers = [(w) => new RegExp(`\\b${esc(w)}\\b`), (w) => new RegExp(`\\b${esc(w)}`), (w) => new RegExp(esc(w))]
    let matches = []
    for (const tier of tiers) {
      const res = words.map(tier)
      matches = glossary.filter((e) => res.every((re) => re.test(searchText(e))))
      if (matches.length) break
    }
    // Entries whose name matches come before ones that only mention it.
    const named = (e) => e.terms.some((t) => t.toLowerCase().includes(words[0]))
    return [...matches.filter(named), ...matches.filter((e) => !named(e))]
  }, [query])

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

      <div className="glossary-search">
        <input
          type="search"
          value={query}
          onChange={(e) => setParams(e.target.value ? { q: e.target.value } : {}, { replace: true })}
          placeholder="Search terms and definitions, e.g. SECO, abort, rover"
          aria-label="Search the glossary"
        />
        <span className="glossary-search-count">
          {query ? `${results.length} of ${glossary.length}` : `${glossary.length} terms`}
        </span>
      </div>

      {results.length === 0 && (
        <p className="glossary-empty">
          Nothing matches &ldquo;{query}&rdquo;.{' '}
          <ReportIssueButton title={`Glossary: add "${query}"`} body={`Please add "${query}" to the glossary.`}>
            Suggest it as a new term
          </ReportIssueButton>
        </p>
      )}

      <section className="glossary-index">
        {results.map((entry) => (
          <article key={entry.id} className="glossary-entry" id={entry.id}>
            <h3>{entry.terms[0]}</h3>
            {entry.terms.length > 1 && (
              <p className="glossary-aliases">also: {entry.terms.slice(1).join(', ')}</p>
            )}
            <GlossaryAbbr entry={entry} />
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
            {hasDetailPage(entry) && (
              <Link to={`/glossary/${entry.id}`} className="glossary-read-more">
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
