// Anonymous site statistics: counts only, sent to our server's /api/stat
// (worker/index.js keeps them as totals by day). No cookies, no visitor id,
// nothing about who you are; a page, a mission, a highlight or a photo, and
// how many minutes of tape were played, by mission hour.

const queue = []
let timer = null

function flush() {
  timer = null
  if (!queue.length) return
  const body = JSON.stringify(queue.splice(0, 20))
  try {
    if (!navigator.sendBeacon || !navigator.sendBeacon('/api/stat', new Blob([body], { type: 'application/json' })))
      fetch('/api/stat', { method: 'POST', body, keepalive: true, headers: { 'Content-Type': 'application/json' } }).catch(() => {})
  } catch {}
  if (queue.length) timer = setTimeout(flush, 1000)
}

export function track(kind, mission = '', item = '', n = 1) {
  if (typeof window === 'undefined' || /^(localhost|127\.)/.test(location.hostname)) return
  const m = /^\d+$/.test(String(mission)) ? String(mission).padStart(2, '0') : String(mission || '')   // ("8" and "08" alike)
  queue.push({ kind, mission: m, item: item ? String(item) : '', n })
  if (!timer) timer = setTimeout(flush, 2000)
}

if (typeof window !== 'undefined') {
  addEventListener('pagehide', flush)
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flush() })
}

// Minutes of tape played, counted as they're heard and sent a minute at a time per mission hour.
const heard = new Map() // "mission|hour" -> seconds not yet sent
export function trackListening(mission, getSeconds, seconds) {
  const hour = Math.floor(getSeconds / 3600)
  const key = `${mission}|${hour}`
  const s = (heard.get(key) || 0) + seconds
  if (s >= 60) {
    track('listen', mission, String(hour), Math.floor(s / 60))
    heard.set(key, s % 60)
  } else heard.set(key, s)
}
