import { usePlayer } from '../audio/PlayerContext'

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

// Controls for the shared app-wide player. When another mission (or no
// mission) is loaded, this shows the page's cued clip and pressing play
// hands that clip to the player.
export default function AudioPlayer({ mission, clips, index }) {
  const player = usePlayer()
  const loaded =
    player.session?.mission.id === mission.id && player.session.index === index

  function togglePlay() {
    if (loaded) player.toggle()
    else player.play(mission, clips, index)
  }

  function handleSeek(e) {
    if (!loaded || !player.duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    player.seek(((e.clientX - rect.left) / rect.width) * player.duration)
  }

  const playing = loaded && player.playing
  const loading = loaded && player.loading
  const error = loaded && player.error
  const current = loaded ? player.currentTime : 0
  const duration = loaded ? player.duration : 0
  const progress = duration ? (current / duration) * 100 : 0

  return (
    <div className="audio-player">
      <button
        type="button"
        className="play-button"
        onClick={togglePlay}
        disabled={error}
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
