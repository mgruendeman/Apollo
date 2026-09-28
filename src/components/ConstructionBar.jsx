import { missions } from '../data/missions'

const onTapes = missions.filter((m) => m.timeline).map((m) => m.number)
const tapeList = `Apollo ${onTapes.length > 1 ? `${onTapes.slice(0, -1).join(', ')} and ${onTapes[onTapes.length - 1]}` : onTapes[0]}`

// On every page: the site is still being built, and where it's at.
export default function ConstructionBar() {
  return (
    <div className="construction-bar" role="note">
      <span aria-hidden="true">🚧</span> <strong>Under construction.</strong> {tapeList} play from NASA&apos;s tapes while I
      check their transcripts; the other missions are clips for now. Each mission&apos;s page shows where it&apos;s at.
    </div>
  )
}
