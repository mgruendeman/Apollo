import { useMemo } from 'react'
import { classifyEventType, EVENT_TYPE_META } from '../data/eventType'
import { parseGet, tapeChapters } from '../lib/missionIndex'
import { formatGetSigned } from '../lib/missionTape'
import { photosByHighlight } from '../data/photos'
import { PHASES } from '../data/phases'
import PhaseIcon from './PhaseIcon'

const HOUR = 3600
const MILESTONE_PHASES = new Set(['launch', 'landing', 'ascent', 'splashdown'])
const endOf = (s) => s.get + (s.to - s.from) * s.rate

// The whole mission on the tapes, as an index: chapters by mission day and
// flight phase, and in each the hours that have a recording, each opening
// with its first words. Picking one plays the tapes from there.
export default function TapeTimeline({ mission, timeline, get, onSeek }) {
  const chapters = useMemo(() => {
    const segments = [...timeline.segments].sort((a, b) => a.get - b.get)
    const from = Math.min(0, segments[0].get)
    const highlights = (mission.highlights || []).map((h) => ({ ...h, g: parseGet(h.at) }))
    return tapeChapters(mission, from, mission.durationSeconds).map((ch) => {
      const rows = []
      let recorded = 0
      for (let h = Math.floor(ch.from / HOUR); h * HOUR < ch.to; h++) {
        const a = Math.max(ch.from, h * HOUR), b = Math.min(ch.to, (h + 1) * HOUR)
        const heard = segments.reduce((sum, s) => sum + Math.max(0, Math.min(b, endOf(s)) - Math.max(a, s.get)), 0)
        if (heard < 30) continue
        recorded += heard
        const lines = timeline.lines.filter((l) => l.g >= a && l.g < b && l.c !== 'pao' && !l.n)
        const first = lines[0]
        const highlight = highlights.find((x) => x.g >= a && x.g < b)
        rows.push({
          g: highlight?.g ?? first?.g ?? Math.max(a, segments.find((s) => endOf(s) > a)?.get ?? a),
          preview: first ? `${first.s}: ${first.t}` : null,
          type: highlight ? 'major' : classifyEventType(lines.map((l) => l.t).join(' ')),
          highlight,
        })
      }
      const type = MILESTONE_PHASES.has(ch.phase) || rows.some((r) => r.highlight)
        ? 'major'
        : rows.filter((r) => r.type === 'rest').length * 3 >= rows.length && rows.length ? 'rest' : 'routine'
      return { ...ch, rows, recorded, type }
    })
  }, [mission, timeline])

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
      {chapters.map((ch) => {
        const meta = EVENT_TYPE_META[ch.type]
        const highlight = ch.rows.find((r) => r.highlight)?.highlight
        const hours = ch.recorded / HOUR
        return (
          <details key={ch.from} open={get >= ch.from && get < ch.to} className={meta.className}>
            <summary>
              <span className="chapter-phase">
                <PhaseIcon phase={ch.phase} />
              </span>
              <span className="chapter-get">
                <span>{formatGetSigned(ch.from)}</span>
                <span className="chapter-get-end">to {formatGetSigned(ch.to)}</span>
              </span>
              <span className="chapter-label">
                {meta.icon && <span className="chapter-icon">{meta.icon} </span>}
                {ch.title}
              </span>
              <span className="chapter-count">
                {ch.rows.length === 0 ? 'no recording' : hours >= 1 ? `${hours.toFixed(1)} h recorded` : `${Math.round(ch.recorded / 60)} min recorded`}
              </span>
            </summary>
            {highlight && (
              <blockquote className="chapter-quote">
                <p className="chapter-quote-title">{highlight.title}</p>
              </blockquote>
            )}
            <ol>
              {ch.rows.map((r) => (
                <TapeRow key={r.g} row={r} chapterLabel={ch.title} isActive={get >= r.g && get < r.g + HOUR} onSelect={() => onSeek(r.g)} />
              ))}
            </ol>
          </details>
        )
      })}
    </section>
  )
}

function TapeRow({ row, chapterLabel, isActive, onSelect }) {
  const meta = EVENT_TYPE_META[row.type]
  const photo = row.highlight && photosByHighlight[row.highlight.id]
  const text = row.highlight ? row.highlight.title : row.preview || chapterLabel
  return (
    <li>
      <button
        type="button"
        className={['moment-item', isActive && 'is-active', row.type === 'routine' && 'is-routine'].filter(Boolean).join(' ')}
        onClick={onSelect}
      >
        <span className="moment-get">{formatGetSigned(row.g)}</span>
        {meta.icon && <span className="moment-icon">{meta.icon}</span>}
        <span className="moment-title">{text.slice(0, row.type === 'routine' ? 70 : 100)}</span>
        {photo && <img className="moment-thumb" src={`${import.meta.env.BASE_URL}${photo.src}`} alt="" loading="lazy" />}
      </button>
    </li>
  )
}
