import { useEffect, useState } from 'react'
import { REACTIONS, reactionsAvailable, topReactions } from '../lib/reactions'

// The mission's most-reacted transcript lines; tap one to hear it.
export default function ListenerFavourites({ missionId, onPick }) {
  const [top, setTop] = useState([])
  useEffect(() => {
    if (!reactionsAvailable) return undefined
    let live = true
    topReactions(missionId).then((rows) => live && setTop(rows))
    return () => {
      live = false
    }
  }, [missionId])
  if (!top.length) return null
  return (
    <section className="listener-favourites">
      <h2>Listener favourites</h2>
      <ol>
        {top.slice(0, 10).map((r) => {
          const counts = {}
          for (const e of (r.emojis || '').split(' ')) if (e) counts[e] = (counts[e] || 0) + 1
          return (
            <li key={r.line}>
              <button type="button" onClick={() => onPick(r.clip, r.get)}>
                <span className="fav-emojis">
                  {REACTIONS.filter(([e]) => counts[e]).map(([e, label]) => (
                    <span key={e} title={label}>
                      {e} {counts[e]}
                    </span>
                  ))}
                </span>
                <span className="fav-line">
                  <span className="fav-meta">
                    {r.speaker} · GET {r.get}
                  </span>
                  {r.text}
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
