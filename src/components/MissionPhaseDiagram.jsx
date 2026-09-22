import { PHASES } from '../data/phases'

export default function MissionPhaseDiagram({ phase }) {
  const p = PHASES[phase] || PHASES['transit-to-moon']

  return (
    <div className="phase-diagram">
      <svg viewBox="0 0 100 100" role="img" aria-label={`Currently: ${p.label}`}>
        <path
          d="M 16 44 Q 50 5 84 34"
          className="phase-path"
          fill="none"
        />
        <path
          d="M 84 40 Q 50 95 16 56"
          className="phase-path"
          fill="none"
        />
        <circle cx="10" cy="50" r="8" className="phase-earth" />
        <circle cx="90" cy="42" r="4.5" className="phase-moon" />
        <circle cx={p.x} cy={p.y} r="2.4" className="phase-marker" />
      </svg>
      <p className="phase-label">{p.label}</p>
    </div>
  )
}
