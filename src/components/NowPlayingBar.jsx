import { Link, useLocation } from 'react-router-dom'
import { usePlayer } from '../audio/PlayerContext'
import { stripSourcePrefix } from '../lib/sourceLabel'

export default function NowPlayingBar() {
  const player = usePlayer()
  const { pathname } = useLocation()
  if (!player.session) return null
  const { mission } = player.session
  if (pathname === `/mission/${mission.id}`) return null

  const progress = player.duration ? (player.currentTime / player.duration) * 100 : 0

  return (
    <>
      <div className="now-playing-spacer" />
      <div className="now-playing">
        <div className="now-playing-progress" style={{ width: `${progress}%` }} />
        <button
          type="button"
          className="play-button now-playing-toggle"
          onClick={player.toggle}
          aria-label={player.playing ? 'Pause' : 'Play'}
        >
          {player.playing ? '❚❚' : '▶'}
        </button>
        <Link to={`/mission/${mission.id}`} className="now-playing-info">
          <span className="now-playing-title">
            {mission.name} · GET {player.clip.get}
          </span>
          <span className="now-playing-sub">{stripSourcePrefix(player.clip.sourceLabel)}</span>
        </Link>
      </div>
    </>
  )
}
