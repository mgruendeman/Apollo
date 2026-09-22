import { createContext, useContext, useEffect, useRef, useState } from 'react'
import { stripSourcePrefix } from '../lib/sourceLabel'

const PlayerContext = createContext(null)

// One <audio> element for the whole app, mounted above the router, so
// playback carries on while you browse the home page or the glossary.
export function PlayerProvider({ children }) {
  const audioRef = useRef(null)
  const wantPlay = useRef(false)
  const pendingSeek = useRef(null)
  const [session, setSession] = useState(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [continuous, setContinuous] = useState(true)

  const clip = session ? session.clips[session.index] : null
  const hasNext = !!session && session.index < session.clips.length - 1
  const hasPrevious = !!session && session.index > 0

  function startPlayback() {
    audioRef.current?.play().catch(() => setError(true))
  }

  function play(mission, clips, index, startAt = null) {
    if (session && session.mission.id === mission.id && session.index === index) {
      if (startAt != null) audioRef.current.currentTime = startAt
      startPlayback()
      return
    }
    wantPlay.current = true
    pendingSeek.current = startAt
    setSession({ mission, clips, index })
  }

  function goTo(index) {
    if (!session || index < 0 || index >= session.clips.length) return
    wantPlay.current = true
    pendingSeek.current = null
    setSession({ ...session, index })
  }

  // Moves to a clip without starting it (the live "happening now" jump).
  function cue(mission, clips, index) {
    wantPlay.current = false
    pendingSeek.current = null
    setSession({ mission, clips, index })
  }

  function toggle() {
    if (playing) audioRef.current?.pause()
    else startPlayback()
  }

  function seek(seconds) {
    if (audioRef.current) audioRef.current.currentTime = seconds
  }

  // The new src is already on the element by the time effects run, so a
  // clip change that should keep playing can start it here.
  useEffect(() => {
    if (clip && wantPlay.current) {
      wantPlay.current = false
      startPlayback()
    }
  }, [clip])

  // Lock-screen / headphone controls, so playback survives the screen
  // turning off on phones.
  useEffect(() => {
    if (!('mediaSession' in navigator) || !clip) return
    navigator.mediaSession.metadata = new MediaMetadata({
      title: `GET ${clip.get} · ${stripSourcePrefix(clip.sourceLabel)}`,
      artist: session.mission.name,
      album: 'Apollo Audio Archive',
    })
    navigator.mediaSession.setActionHandler('play', startPlayback)
    navigator.mediaSession.setActionHandler('pause', () => audioRef.current?.pause())
    navigator.mediaSession.setActionHandler('previoustrack', hasPrevious ? () => goTo(session.index - 1) : null)
    navigator.mediaSession.setActionHandler('nexttrack', hasNext ? () => goTo(session.index + 1) : null)
  })

  useEffect(() => {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = playing ? 'playing' : 'paused'
    }
  }, [playing])

  const value = {
    session,
    clip,
    playing,
    currentTime,
    duration,
    loading,
    error,
    continuous,
    setContinuous,
    hasNext,
    hasPrevious,
    play,
    goTo,
    cue,
    toggle,
    seek,
  }

  return (
    <PlayerContext.Provider value={value}>
      {children}
      <audio
        ref={audioRef}
        src={clip?.audioUrl}
        preload="metadata"
        onLoadStart={() => {
          setLoading(true)
          setError(false)
          setCurrentTime(0)
          setDuration(0)
        }}
        onLoadedMetadata={(e) => {
          setDuration(e.currentTarget.duration)
          setLoading(false)
          if (pendingSeek.current != null) {
            e.currentTarget.currentTime = pendingSeek.current
            pendingSeek.current = null
          }
        }}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => {
          setPlaying(false)
          if (continuous && hasNext) goTo(session.index + 1)
        }}
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onError={() => {
          if (!clip) return
          setLoading(false)
          setError(true)
        }}
      />
    </PlayerContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePlayer() {
  return useContext(PlayerContext)
}
