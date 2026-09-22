export default function GlossaryAbbr({ entry }) {
  if (!entry.abbr) return null
  return (
    <p className="glossary-abbr">
      {entry.abbr.map((a) => (
        <span key={a.short}>
          <strong>{a.short}</strong> — {a.full}
        </span>
      ))}
    </p>
  )
}
