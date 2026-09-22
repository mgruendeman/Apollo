import { PHASES } from '../data/phases'

export default function MissionPhaseDiagram({ phase }) {
  const p = PHASES[phase] || PHASES['transit-to-moon']

  return (
    <div className="phase-diagram">
      <svg viewBox="0 0 200 100" role="img" aria-label={`Currently: ${p.label}`}>
        {/* translunar / transearth transfer paths */}
        <path d="M 38 36 Q 100 8 166 41" className="phase-path" fill="none" />
        <path d="M 166 59 Q 100 92 38 64" className="phase-path" fill="none" />

        {/* earth orbit ring */}
        <circle cx="26" cy="50" r="18" className="phase-orbit-ring" fill="none" />
        {/* lunar orbit ring */}
        <circle cx="174" cy="50" r="12" className="phase-orbit-ring" fill="none" />

        <circle cx="26" cy="50" r="9" className="phase-earth" />
        <circle cx="174" cy="50" r="5.5" className="phase-moon" />

        <circle cx={p.x} cy={p.y} r="3" className="phase-marker" />
      </svg>
      <p className="phase-label">{p.label}</p>
    </div>
  )
}
