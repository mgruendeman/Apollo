import { PHASES } from '../data/phases'

// Small line icons for each mission phase, drawn in the current text colour.
const PATHS = {
  // rocket with flame
  launch: (
    <>
      <path d="M12 2c2.6 2.2 3.8 5.4 3.8 9.2V16H8.2v-4.8C8.2 7.4 9.4 4.2 12 2z" />
      <path d="M8.2 12.5 5.5 15v2.5l2.7-1.5M15.8 12.5l2.7 2.5v2.5l-2.7-1.5" />
      <path d="M10.3 18.5 12 22l1.7-3.5" />
      <circle cx="12" cy="8.5" r="1.4" />
    </>
  ),
  // Earth with an orbit ring
  'earth-orbit': (
    <>
      <circle cx="12" cy="12" r="5.5" />
      <ellipse cx="12" cy="12" rx="10.5" ry="3.6" transform="rotate(-20 12 12)" />
    </>
  ),
  // Earth to Moon, outbound
  'transit-to-moon': (
    <>
      <circle cx="5" cy="15" r="3" />
      <path d="M18.5 4.5a3.8 3.8 0 1 0 1.5 6 3 3 0 0 1-1.5-6z" />
      <path d="M8.5 12.5c2.5-3 5-4.2 7.5-4.5" strokeDasharray="1.6 2" />
      <path d="m13.8 6.6 2.4 1.4-1.8 2" />
    </>
  ),
  // Moon with an orbit ring
  'lunar-orbit': (
    <>
      <circle cx="12" cy="12" r="5" />
      <circle cx="10.3" cy="10.8" r="1" />
      <circle cx="13.6" cy="13.8" r="0.8" />
      <ellipse cx="12" cy="12" rx="10.5" ry="3.4" transform="rotate(20 12 12)" />
    </>
  ),
  // lander coming down
  landing: (
    <>
      <path d="M8.5 9h7l1 4h-9z" />
      <path d="M8.5 13 6 17M15.5 13l2.5 4M4.5 17h3M16.5 17h3" />
      <path d="M12 2v4.5M10 4.8 12 6.8l2-2" />
      <path d="M2 21h20" />
    </>
  ),
  // flag on the ground
  surface: (
    <>
      <path d="M7 21V3" />
      <path d="M7 4h11l-2.5 3.5L18 11H7" />
      <path d="M2 21h20" />
    </>
  ),
  // ascent stage lifting off
  ascent: (
    <>
      <path d="M8.5 8h7l1 4h-9z" />
      <path d="M12 16.5V22M10 19.2l2-2 2 2" />
      <path d="M2 14.5h4M18 14.5h4" />
    </>
  ),
  // Moon to Earth, homeward
  'transit-to-earth': (
    <>
      <circle cx="19" cy="15" r="3" />
      <path d="M5.5 4.5a3.8 3.8 0 1 1-1.5 6 3 3 0 0 0 1.5-6z" />
      <path d="M15.5 12.5c-2.5-3-5-4.2-7.5-4.5" strokeDasharray="1.6 2" />
      <path d="M10.2 6.6 7.8 8l1.8 2" />
    </>
  ),
  // capsule under a parachute over the water
  splashdown: (
    <>
      <path d="M4 10a8 6.5 0 0 1 16 0z" />
      <path d="M4 10l6.5 7M20 10l-6.5 7M12 10v7" />
      <path d="M10 17h4l-.8 2.5h-2.4z" />
      <path d="M2 22c2-1.2 4-1.2 6 0s4 1.2 6 0 4-1.2 6 0" />
    </>
  ),
}

export default function PhaseIcon({ phase, className = 'phase-icon' }) {
  const paths = PATHS[phase]
  if (!paths) return null
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label={PHASES[phase]?.label || phase}
    >
      <title>{PHASES[phase]?.label || phase}</title>
      {paths}
    </svg>
  )
}
