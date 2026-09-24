import { useEffect, useState } from 'react'
import { API_BASE } from '../config'
import { visitorId } from './likes'

// Emoji reactions to transcript lines, one of each per browser per line
// (same visitor id as likes). They feed each mission's "Listener favourites".
export const REACTIONS = [
  ['🤣', 'Funny'],
  ['😲', 'Wow'],
  ['‼️', 'Big moment'],
  ['❤️', 'Moving'],
  ['😬', 'Tense'],
]
export const reactionsAvailable = !!API_BASE

// A line's id: its clip, time and speaker, plus a short hash of the words,
// so it survives the transcript being re-timed.
export function lineId(clip, line) {
  let h = 5381
  for (const ch of line.text) h = ((h << 5) + h + ch.codePointAt(0)) >>> 0
  return `${clip}|${line.get}|${line.speaker.replace(/[^A-Za-z0-9]/g, '')}|${h.toString(36)}`.slice(0, 120)
}

// { [lineId]: { [emoji]: { n, mine } } } for one clip, with a toggle. `clip`
// can list several clips, comma-separated (the whole-mission transcript
// spans hours; each line then names its own clip as line.clip).
export function useClipReactions(mission, clip) {
  const [state, setState] = useState({})
  useEffect(() => {
    if (!reactionsAvailable || !clip) return undefined
    let live = true
    Promise.all(
      clip.split(',').map((c) =>
        fetch(`${API_BASE}/reactions?mission=${mission}&clip=${encodeURIComponent(c)}&visitor=${visitorId()}`)
          .then((r) => (r.ok ? r.json() : { reactions: [] }))
          .catch(() => ({ reactions: [] })),
      ),
    ).then((results) => {
      if (!live) return
      const next = {}
      for (const { reactions } of results)
        for (const r of reactions) (next[r.line] ||= {})[r.emoji] = { n: r.n, mine: !!r.mine }
      setState(next)
    })
    return () => {
      live = false
    }
  }, [mission, clip])

  const clipOf = (line) => line.clip || clip
  async function toggle(line, emoji) {
    const id = lineId(clipOf(line), line)
    const was = state[id]?.[emoji] || { n: 0, mine: false }
    const on = !was.mine
    const set = (v) => setState((s) => ({ ...s, [id]: { ...(s[id] || {}), [emoji]: v } }))
    set({ n: Math.max(0, was.n + (on ? 1 : -1)), mine: on })
    try {
      const r = await fetch(`${API_BASE}/reactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ line: id, clip: clipOf(line), mission, emoji, on, visitor: visitorId(), get: line.get, speaker: line.speaker, text: line.text }),
      })
      if (!r.ok) throw new Error(r.status)
      const { count } = await r.json()
      set({ n: count, mine: on })
    } catch {
      set(was)
    }
  }
  return { get: (line) => state[lineId(clipOf(line), line)] || {}, toggle }
}

export async function topReactions(mission) {
  try {
    const r = await fetch(`${API_BASE}/reactions/top?mission=${mission}`)
    return r.ok ? (await r.json()).top : []
  } catch {
    return []
  }
}
