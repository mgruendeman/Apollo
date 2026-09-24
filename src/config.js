// Where "report a problem" forms are sent: our server's /api/reports (saved
// for the reviewers' Reports page), or VITE_REPORT_ENDPOINT if set. With
// neither (GitHub Pages), reports open as a pre-filled GitHub issue.
// The site's own server (worker/index.js) runs where the site is served from
// the root (Cloudflare), not on GitHub Pages; features that need it switch
// off where it isn't.
export const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.BASE_URL === '/' ? '/api' : '')

export const REPORT_ENDPOINT = import.meta.env.VITE_REPORT_ENDPOINT || (API_BASE ? `${API_BASE}/reports` : '')

export const REPO_URL = 'https://github.com/mgruendeman/Apollo'

// Where our processed media (cleaned photos, audio) is served from: the
// Cloudflare R2 bucket's public address. Empty = show the original scans.
// r2.dev is Cloudflare's rate-limited test address; switch to our own domain
// (e.g. media.<domain>) before launch.
export const MEDIA_URL = (import.meta.env.VITE_MEDIA_URL || 'https://pub-7070d40e34dc47deaf91a77ffc426969.r2.dev').replace(/\/$/, '')
