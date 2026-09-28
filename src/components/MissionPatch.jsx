import { patchFor } from '../data/patches'

// The mission's official emblem, beside its name at the top of its page.
export default function MissionPatch({ mission }) {
  const patch = patchFor(mission.id)
  if (!patch) return null
  return <img className="mission-header-patch" src={patch} alt={`${mission.name} mission emblem`} />
}
