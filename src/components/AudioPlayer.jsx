import { useRef, useState } from 'react'

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

// Keyed by moment.id from the parent, so a new moment mounts a fresh
// instance instead of needing an effect to reset playback state.
export default function AudioPlayer({ moment }) {
  const audioRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [duration, setDuration] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  function togglePlay() {
    const audio = audioRef.current
    if (!audio) return
    if (playing) {
      audio.pause()
    } else {
      audio.play().catch(() => setError(true))
    }
  }

  function handleSeek(e) {
    const audio = audioRef.current
    if (!audio || !duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    const ratio = (e.clientX - rect.left) / rect.width
    audio.currentTime = ratio * duration
  }

  const progress = duration ? (current / duration) * 100 : 0

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={moment.audioUrl}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onLoadedMetadata={(e) => {
          setDuration(e.currentTarget.duration)
          setLoading(false)
        }}
        onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)}
        onError={() => {
          setLoading(false)
          setError(true)
        }}
      />
      <button
        type="button"
        className="play-button"
        onClick={togglePlay}
        disabled={loading || error}
        aria-label={playing ? 'Pause' : 'Play'}
      >
        {loading ? '…' : playing ? '❚❚' : '▶'}
      </button>
      <div className="scrub" onClick={handleSeek} role="presentation">
        <div className="scrub-track">
          <div className="scrub-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
      <div className="times">
        <span>{formatTime(current)}</span>
        <span>{error ? 'unavailable' : formatTime(duration)}</span>
      </div>
    </div>
  )
}
