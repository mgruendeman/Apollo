import { useEffect, useRef, useState } from 'react'

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

// Keyed by moment.id from the parent, so a new moment mounts a fresh
// instance instead of needing an effect to reset playback state.
export default function AudioPlayer({
  moment,
  title,
  missionName,
  autoPlay = false,
  onEnded,
  onNext,
  onPrevious,
  hasNext = false,
  hasPrevious = false,
  onTimeUpdate,
  seekRequest,
}) {
  const audioRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [duration, setDuration] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // Starting playback of a freshly-mounted track (continuous mode advancing
  // to the next clip) is a side effect on the audio element, not state
  // derived during render, so it belongs in an effect.
  useEffect(() => {
    if (autoPlay && audioRef.current) {
      audioRef.current.play().catch(() => setError(true))
    }
  }, [autoPlay])

  // Media Session integration is what lets playback (and its lock-screen
  // controls) survive the screen turning off or the tab being backgrounded
  // on phones — without it, mobile browsers are much more likely to treat
  // this as an ordinary inactive tab and suspend it.
  useEffect(() => {
    if (!('mediaSession' in navigator)) return
    navigator.mediaSession.metadata = new MediaMetadata({
      title: title || moment.get,
      artist: missionName || 'Apollo Audio Archive',
      album: 'Apollo Audio Archive',
    })
    navigator.mediaSession.setActionHandler('play', () => {
      audioRef.current?.play().catch(() => setError(true))
    })
    navigator.mediaSession.setActionHandler('pause', () => {
      audioRef.current?.pause()
    })
    navigator.mediaSession.setActionHandler(
      'previoustrack',
      hasPrevious ? () => onPrevious?.() : null,
    )
    navigator.mediaSession.setActionHandler(
      'nexttrack',
      hasNext ? () => onNext?.() : null,
    )
    return () => {
      navigator.mediaSession.setActionHandler('play', null)
      navigator.mediaSession.setActionHandler('pause', null)
      navigator.mediaSession.setActionHandler('previoustrack', null)
      navigator.mediaSession.setActionHandler('nexttrack', null)
    }
  }, [moment, title, missionName, hasNext, hasPrevious, onNext, onPrevious])

  useEffect(() => {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = playing ? 'playing' : 'paused'
    }
  }, [playing])

  // The channel toggle can't switch to different audio — air-to-ground,
  // onboard and PAO chatter are all baked into the same single recording
  // — but it can jump playback to where that channel's dialogue starts.
  useEffect(() => {
    if (seekRequest == null || !audioRef.current) return
    audioRef.current.currentTime = seekRequest.seconds
  }, [seekRequest])

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
        onEnded={() => {
          setPlaying(false)
          onEnded?.()
        }}
        onLoadedMetadata={(e) => {
          setDuration(e.currentTarget.duration)
          setLoading(false)
        }}
        onTimeUpdate={(e) => {
          setCurrent(e.currentTarget.currentTime)
          onTimeUpdate?.(e.currentTarget.currentTime)
        }}
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
