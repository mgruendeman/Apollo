import { useEffect, useState } from 'react'
import { API_BASE } from '../config'

// Likes without accounts: each browser gets a random visitor id, kept in its
// storage, and the server records one like per photo per id (and caps how
// many likes one connection can give per day).
const KEY = 'apollo-visitor'
let visitor = null
export function visitorId() {
  if (visitor) return visitor
  try {
    visitor = localStorage.getItem(KEY)
  } catch {
    /* storage blocked: an id for this visit only */
  }
  if (!visitor || !/^[A-Za-z0-9-]{16,64}$/.test(visitor)) {
    visitor = crypto.randomUUID()
    try {
      localStorage.setItem(KEY, visitor)
    } catch {
      /* not kept */
    }
  }
  return visitor
}

export const likesAvailable = !!API_BASE
const known = new Map() // photo -> { count, liked }
const listeners = new Set()
const notify = () => listeners.forEach((fn) => fn())

// Counts (and whether this browser liked them) for a set of photos, batched.
let pending = new Set()
let timer = null
function request(ids) {
  for (const id of ids) if (!known.has(id)) pending.add(id)
  if (!pending.size || timer) return
  timer = setTimeout(async () => {
    const batch = [...pending].slice(0, 300)
    pending = new Set([...pending].slice(300))
    timer = null
    try {
      const r = await fetch(`${API_BASE}/likes?ids=${encodeURIComponent(batch.join(','))}&visitor=${visitorId()}`)
      if (!r.ok) throw new Error(r.status)
      const { counts, mine } = await r.json()
      const liked = new Set(mine)
      for (const id of batch) known.set(id, { count: counts[id] || 0, liked: liked.has(id) })
      notify()
    } catch {
      /* no server here: likes stay hidden */
    }
    if (pending.size) request([])
  }, 60)
}

export function useLikes(ids) {
  const [, setTick] = useState(0)
  const key = ids.join(',')
  useEffect(() => {
    if (!likesAvailable) return undefined
    const fn = () => setTick((t) => t + 1)
    listeners.add(fn)
    request(key ? key.split(',') : [])
    return () => listeners.delete(fn)
  }, [key])
  return (id) => known.get(id)
}

export async function toggleLike(id) {
  const now = known.get(id) || { count: 0, liked: false }
  const next = { count: now.count + (now.liked ? -1 : 1), liked: !now.liked }
  known.set(id, next) // show it straight away
  notify()
  try {
    const r = await fetch(`${API_BASE}/likes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photo: id, visitor: visitorId(), like: next.liked }),
    })
    if (!r.ok) throw new Error(r.status)
    const { count, liked } = await r.json()
    known.set(id, { count, liked })
  } catch {
    known.set(id, now)
  }
  notify()
}

// The most-liked photos of a mission (ids like AS11-…), most first.
export async function topLiked(missionId) {
  try {
    const r = await fetch(`${API_BASE}/likes/top?prefix=AS${missionId}-`)
    if (!r.ok) return []
    return (await r.json()).top
  } catch {
    return []
  }
}

// One id per frame, so NASA's version and the scan of the same frame share
// their likes ("as11-40-5875", "AS11-40-5875" -> "AS11-40-5875").
export function likeId(photo) {
  const m = /^(?:KSC-)?AS(\d\d)-0*(\d+[A-D]?)-0*(\d+[A-D]?)/i.exec(photo.key)
  return m ? `AS${m[1]}-${m[2].toUpperCase()}-${m[3].toUpperCase()}` : photo.key
}
