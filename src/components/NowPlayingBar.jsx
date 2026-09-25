import { Link, useLocation } from 'react-router-dom'
import { usePlayer } from '../audio/PlayerContext'
import { stripSourcePrefix } from '../lib/sourceLabel'

export default function NowPlayingBar() {
  const player = usePlayer()
  const { pathname } = useLocation()
  if (!player.session) return null
  const { mission } = player.session
  const route = `/mission/${mission.routeId || mission.id}`
  // On its own mission page the full player is already visible (whole
  // archive recordings keep the bar, since they have no player there).
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
        <Link to={route} className="now-playing-info">
          <span className="now-playing-title">
            {mission.name}
            {player.clip.get && ` · GET ${player.clip.get}`}
          </span>
          <span className="now-playing-sub">{player.clip.chapterTitle || stripSourcePrefix(player.clip.sourceLabel)}</span>
        </Link>
      </div>
    </>
  )
}
