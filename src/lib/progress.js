import { useEffect, useState } from 'react'

// Where each tape mission's work stands (public/progress.json, written by
// pipeline/align_tapes.py): hours recorded, lines, lines corrected by hand,
// lines still flagged for a listen. Fetched once for the whole visit.
let loading = null
function load() {
  loading ??= fetch(`${import.meta.env.BASE_URL}progress.json`)
    .then((r) => (r.ok ? r.json() : {}))
    .catch(() => ({}))
  return loading
}

export function useProgress() {
  const [progress, setProgress] = useState(null)
  useEffect(() => {
    let live = true
    load().then((p) => live && setProgress(p))
    return () => {
      live = false
    }
  }, [])
  return progress
}

// What stage a mission is at: 'tapes' (on NASA's tapes, transcript being
// checked), 'clips' (the journals' clips for now) or 'archive' (NASA's
// recordings listed, not yet on the mission clock).
export function stageOf(mission) {
  if (mission.timeline) return 'tapes'
  if (mission.clipsFile) return 'clips'
  return 'archive'
}
