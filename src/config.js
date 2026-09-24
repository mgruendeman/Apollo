// Where "report a problem" forms are sent. Set VITE_REPORT_ENDPOINT at build
// time to a form service that accepts a JSON POST (for example a Formspree
// form URL, https://formspree.io/f/<id>). Left empty, reports open as a
// pre-filled GitHub issue instead.
export const REPORT_ENDPOINT = import.meta.env.VITE_REPORT_ENDPOINT || ''

export const REPO_URL = 'https://github.com/mgruendeman/Apollo'

// Where our processed media (cleaned photos, audio) is served from: the
// Cloudflare R2 bucket's public address. Empty = show the original scans.
// r2.dev is Cloudflare's rate-limited test address; switch to our own domain
// (e.g. media.<domain>) before launch.
export const MEDIA_URL = (import.meta.env.VITE_MEDIA_URL || 'https://pub-7070d40e34dc47deaf91a77ffc426969.r2.dev').replace(/\/$/, '')
