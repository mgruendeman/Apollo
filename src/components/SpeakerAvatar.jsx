import { speakerAvatar } from '../data/speakers'

function speakerColor(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash) % 360
  return `hsl(${hue}, 55%, 42%)`
}

function initials(name) {
  const words = name.trim().split(/\s+/)
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[words.length - 1][0]).toUpperCase()
}

// A NASA portrait where we have one, otherwise a colored initials badge.
export default function SpeakerAvatar({ name, className = '' }) {
  const avatar = speakerAvatar(name)
  if (avatar) {
    return <img className={`speaker-avatar ${className}`} src={avatar} alt={name} title={name} />
  }
  return (
    <span className={`speaker-badge ${className}`} style={{ background: speakerColor(name) }} title={name}>
      {initials(name)}
    </span>
  )
}
