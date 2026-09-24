// The site's small server: likes, problem reports, and the photo reviewers'
// marks, kept in a D1 database. Everything else is the static site (the Vite
// build in dist/), served by Cloudflare's asset hosting.
//
// Bindings (wrangler.jsonc): DB (D1), MEDIA (the R2 bucket of cleaned
// photos), ASSETS (the static site). Secrets, set in the Cloudflare dashboard
// (Worker > Settings > Variables and Secrets):
//   REVIEW_PASSWORD  opens the reviewer pages and their API
//   HASH_SALT        any long random text; scrambles IP addresses before
//                    they're used for rate limits (no address is stored)

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS likes (photo TEXT NOT NULL, visitor TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY (photo, visitor))`,
  `CREATE INDEX IF NOT EXISTS likes_photo ON likes (photo)`,
  `CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, subject TEXT, message TEXT NOT NULL,
     context TEXT, contact TEXT, page TEXT, status TEXT NOT NULL DEFAULT 'new')`,
  `CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS limits (key TEXT PRIMARY KEY, n INTEGER NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS reactions (line TEXT NOT NULL, emoji TEXT NOT NULL, visitor TEXT NOT NULL, at TEXT NOT NULL,
     PRIMARY KEY (line, emoji, visitor))`,
  `CREATE TABLE IF NOT EXISTS reaction_lines (line TEXT PRIMARY KEY, mission TEXT NOT NULL, clip TEXT NOT NULL,
     get TEXT, speaker TEXT, text TEXT)`,
  `CREATE INDEX IF NOT EXISTS reaction_lines_clip ON reaction_lines (mission, clip)`,
]
const LIMITS = { like: 1000, report: 20, react: 5000 } // per scrambled IP address, per day
// 🤣 funny, 😲 wow, ‼️ big moment, ❤️ moving, 😬 tense (src/lib/reactions.js has the same list)
const EMOJIS = ['🤣', '😲', '‼️', '❤️', '😬']
const SESSION_DAYS = 30

let schemaReady = null
function ready(env) {
  schemaReady ??= env.DB.batch(SCHEMA.map((s) => env.DB.prepare(s))).catch((e) => {
    schemaReady = null
    throw e
  })
  return schemaReady
}

const json = (data, status = 200, headers = {}) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers } })
const bad = (status, error) => json({ error }, status)
const today = () => new Date().toISOString().slice(0, 10)

async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

// Count one action against today's limit for this (scrambled) address.
async function underLimit(env, request, kind) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown'
  const key = `${kind}:${today()}:${(await sha256(`${env.HASH_SALT || ''}|${today()}|${ip}`)).slice(0, 32)}`
  const row = await env.DB.prepare(
    `INSERT INTO limits (key, n) VALUES (?1, 1) ON CONFLICT(key) DO UPDATE SET n = n + 1 RETURNING n`,
  ).bind(key).first()
  return row.n <= LIMITS[kind]
}

// ---------- reviewer sign-in: a password, then a signed cookie ----------
async function hmac(secret, text) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(text))
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
function sameText(a, b) {
  if (a.length !== b.length) return false
  let d = 0
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return d === 0
}
async function isReviewer(env, request) {
  const secret = env.REVIEW_PASSWORD
  if (!secret) return false
  const auth = request.headers.get('Authorization') || ''
  if (auth.startsWith('Bearer ') && sameText(auth.slice(7), secret)) return true   // the pipeline's scripts
  const cookie = /(?:^|;\s*)review=([^;]+)/.exec(request.headers.get('Cookie') || '')
  if (!cookie) return false
  const [expires, sig] = decodeURIComponent(cookie[1]).split('.')
  return Number(expires) > Date.now() && sameText(sig || '', await hmac(secret, `review:${expires}`))
}

async function login(env, request) {
  const { password } = await request.json().catch(() => ({}))
  if (!env.REVIEW_PASSWORD) return bad(503, 'Reviewing is not set up yet (no REVIEW_PASSWORD).')
  if (typeof password !== 'string' || !sameText(password, env.REVIEW_PASSWORD)) {
    await new Promise((r) => setTimeout(r, 800))   // slow down guessing
    return bad(401, 'Wrong password.')
  }
  const expires = Date.now() + SESSION_DAYS * 864e5
  const value = encodeURIComponent(`${expires}.${await hmac(env.REVIEW_PASSWORD, `review:${expires}`)}`)
  return json({ ok: true }, 200, {
    'Set-Cookie': `review=${value}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Strict`,
  })
}

// ---------- likes ----------
const PHOTO = /^[A-Za-z0-9_.-]{3,60}$/
const VISITOR = /^[A-Za-z0-9-]{16,64}$/

async function getLikes(env, url) {
  const ids = (url.searchParams.get('ids') || '').split(',').filter((id) => PHOTO.test(id)).slice(0, 300)
  const visitor = url.searchParams.get('visitor') || ''
  if (!ids.length) return json({ counts: {}, mine: [] })
  const marks = ids.map((_, i) => `?${i + 1}`).join(',')
  const counts = await env.DB.prepare(`SELECT photo, COUNT(*) AS n FROM likes WHERE photo IN (${marks}) GROUP BY photo`)
    .bind(...ids).all()
  let mine = []
  if (VISITOR.test(visitor)) {
    const rows = await env.DB.prepare(`SELECT photo FROM likes WHERE visitor = ?${ids.length + 1} AND photo IN (${marks})`)
      .bind(...ids, visitor).all()
    mine = rows.results.map((r) => r.photo)
  }
  return json({ counts: Object.fromEntries(counts.results.map((r) => [r.photo, r.n])), mine })
}

async function topLikes(env, url) {
  const prefix = (url.searchParams.get('prefix') || '').toUpperCase()   // e.g. AS11- or as11-
  if (!/^[A-Z0-9-]{2,12}$/.test(prefix)) return bad(400, 'prefix needed, e.g. AS11-')
  const rows = await env.DB.prepare(
    `SELECT photo, COUNT(*) AS n FROM likes WHERE upper(photo) LIKE ?1 GROUP BY photo ORDER BY n DESC LIMIT 200`,
  ).bind(`${prefix}%`).all()
  return json({ top: rows.results })
}

async function setLike(env, request) {
  const { photo, visitor, like } = await request.json().catch(() => ({}))
  if (!PHOTO.test(photo || '') || !VISITOR.test(visitor || '')) return bad(400, 'photo and visitor needed')
  if (like) {
    if (!(await underLimit(env, request, 'like'))) return bad(429, 'Too many likes from this connection today.')
    await env.DB.prepare(`INSERT OR IGNORE INTO likes (photo, visitor, at) VALUES (?1, ?2, ?3)`)
      .bind(photo, visitor, new Date().toISOString()).run()
  } else {
    await env.DB.prepare(`DELETE FROM likes WHERE photo = ?1 AND visitor = ?2`).bind(photo, visitor).run()
  }
  const row = await env.DB.prepare(`SELECT COUNT(*) AS n FROM likes WHERE photo = ?1`).bind(photo).first()
  return json({ photo, count: row.n, liked: !!like })
}

// ---------- reactions to transcript lines ----------
const LINE = /^[A-Za-z0-9_.:|~-]{6,120}$/
const MISSION = /^\d{2}$/

async function clipReactions(env, url) {
  const mission = url.searchParams.get('mission') || ''
  const clipId = url.searchParams.get('clip') || ''
  const visitor = url.searchParams.get('visitor') || ''
  if (!MISSION.test(mission) || !PHOTO.test(clipId)) return bad(400, 'mission and clip needed')
  const rows = await env.DB.prepare(`SELECT r.line, r.emoji, COUNT(*) AS n, SUM(r.visitor = ?3) AS mine
      FROM reactions r JOIN reaction_lines l ON l.line = r.line
      WHERE l.mission = ?1 AND l.clip = ?2 GROUP BY r.line, r.emoji`).bind(mission, clipId, visitor).all()
  return json({ reactions: rows.results })
}

async function topReactions(env, url) {
  const mission = url.searchParams.get('mission') || ''
  if (!MISSION.test(mission)) return bad(400, 'mission needed')
  const rows = await env.DB.prepare(`SELECT l.line, l.clip, l.get, l.speaker, l.text, COUNT(*) AS total,
      GROUP_CONCAT(r.emoji, ' ') AS emojis
      FROM reactions r JOIN reaction_lines l ON l.line = r.line
      WHERE l.mission = ?1 GROUP BY l.line ORDER BY total DESC, l.get LIMIT 30`).bind(mission).all()
  return json({ top: rows.results })
}

async function setReaction(env, request) {
  const b = await request.json().catch(() => ({}))
  if (!LINE.test(b.line || '') || !VISITOR.test(b.visitor || '') || !EMOJIS.includes(b.emoji) ||
      !MISSION.test(b.mission || '') || !PHOTO.test(b.clip || '')) return bad(400, 'line, clip, mission, emoji and visitor needed')
  if (b.on) {
    if (!(await underLimit(env, request, 'react'))) return bad(429, 'Too many reactions from this connection today.')
    await env.DB.batch([
      env.DB.prepare(`INSERT OR IGNORE INTO reactions (line, emoji, visitor, at) VALUES (?1, ?2, ?3, ?4)`)
        .bind(b.line, b.emoji, b.visitor, new Date().toISOString()),
      env.DB.prepare(`INSERT INTO reaction_lines (line, mission, clip, get, speaker, text) VALUES (?1, ?2, ?3, ?4, ?5, ?6)
        ON CONFLICT(line) DO NOTHING`).bind(b.line, b.mission, b.clip, clip(b.get, 12), clip(b.speaker, 60), clip(b.text, 400)),
    ])
  } else {
    await env.DB.prepare(`DELETE FROM reactions WHERE line = ?1 AND emoji = ?2 AND visitor = ?3`).bind(b.line, b.emoji, b.visitor).run()
  }
  const row = await env.DB.prepare(`SELECT COUNT(*) AS n FROM reactions WHERE line = ?1 AND emoji = ?2`).bind(b.line, b.emoji).first()
  return json({ line: b.line, emoji: b.emoji, count: row.n, on: !!b.on })
}

// ---------- problem reports ----------
const clip = (v, n) => (typeof v === 'string' ? v.slice(0, n) : '')

async function addReport(env, request) {
  const b = await request.json().catch(() => ({}))
  const message = clip(b.message, 4000).trim()
  if (!message) return bad(400, 'message needed')
  if (!(await underLimit(env, request, 'report'))) return bad(429, 'Too many reports from this connection today.')
  await env.DB.prepare(`INSERT INTO reports (at, subject, message, context, contact, page) VALUES (?1, ?2, ?3, ?4, ?5, ?6)`)
    .bind(new Date().toISOString(), clip(b.subject, 300), message, clip(b.context, 4000), clip(b.contact, 200), clip(b.page, 500)).run()
  return json({ ok: true })
}

async function listReports(env, url) {
  const status = url.searchParams.get('status') || 'new'
  const rows = await env.DB.prepare(`SELECT * FROM reports WHERE status = ?1 OR ?1 = 'all' ORDER BY id DESC LIMIT 500`).bind(status).all()
  return json({ reports: rows.results })
}

async function setReport(env, request, id) {
  const { status } = await request.json().catch(() => ({}))
  if (!['new', 'fixed', 'dismissed'].includes(status)) return bad(400, 'status: new, fixed or dismissed')
  await env.DB.prepare(`UPDATE reports SET status = ?1 WHERE id = ?2`).bind(status, Number(id)).run()
  return json({ ok: true })
}

// ---------- review marks ----------
const REVIEW_ID = /^[A-Za-z0-9_.-]{3,60}$/

async function listReviews(env) {
  const rows = await env.DB.prepare(`SELECT id, body, updated FROM reviews`).all()
  return json({ reviews: rows.results.map((r) => ({ id: r.id, updated: r.updated, data: JSON.parse(r.body) })) })
}

async function putReview(env, request, id) {
  if (!REVIEW_ID.test(id)) return bad(400, 'bad id')
  const body = await request.json().catch(() => null)
  if (!body || typeof body !== 'object' || Array.isArray(body)) return bad(400, 'JSON object needed')
  const text = JSON.stringify(body)
  if (text.length > 20000) return bad(413, 'too big')
  const updated = new Date().toISOString()
  await env.DB.prepare(`INSERT INTO reviews (id, body, updated) VALUES (?1, ?2, ?3)
    ON CONFLICT(id) DO UPDATE SET body = excluded.body, updated = excluded.updated`).bind(id, text, updated).run()
  return json({ id, updated })
}

// Cleaned photos for the reviewer page, from our own address so the page's
// live preview can read their pixels.
async function media(env, key) {
  const obj = await env.MEDIA.get(key)
  if (!obj) return new Response('Not found', { status: 404 })
  const headers = new Headers()
  obj.writeHttpMetadata(headers)
  headers.set('Cache-Control', 'private, max-age=3600')
  headers.set('ETag', obj.httpEtag)
  return new Response(obj.body, { headers })
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const { pathname } = url
    const method = request.method
    if (!pathname.startsWith('/api/')) return env.ASSETS.fetch(request)
    try {
      await ready(env)
      if (pathname === '/api/likes' && method === 'GET') return getLikes(env, url)
      if (pathname === '/api/likes/top' && method === 'GET') return topLikes(env, url)
      if (pathname === '/api/likes' && method === 'POST') return setLike(env, request)
      if (pathname === '/api/reports' && method === 'POST') return addReport(env, request)
      if (pathname === '/api/reactions' && method === 'GET') return clipReactions(env, url)
      if (pathname === '/api/reactions/top' && method === 'GET') return topReactions(env, url)
      if (pathname === '/api/reactions' && method === 'POST') return setReaction(env, request)
      if (pathname === '/api/review/login' && method === 'POST') return login(env, request)

      if (pathname.startsWith('/api/review/')) {
        if (!(await isReviewer(env, request))) return bad(401, 'Sign in needed.')
        const rest = pathname.slice('/api/review/'.length)
        if (rest === 'me') return json({ ok: true })
        if (rest === 'marks' && method === 'GET') return listReviews(env)
        if (rest.startsWith('marks/') && method === 'PUT') return putReview(env, request, rest.slice(6))
        if (rest.startsWith('marks/') && method === 'DELETE') {
          await env.DB.prepare(`DELETE FROM reviews WHERE id = ?1`).bind(rest.slice(6)).run()
          return json({ ok: true })
        }
        if (rest === 'reports' && method === 'GET') return listReports(env, url)
        if (rest.startsWith('reports/') && method === 'PUT') return setReport(env, request, rest.slice(8))
        if (rest.startsWith('media/') && method === 'GET') return media(env, rest.slice(6))
      }
      return bad(404, 'No such API.')
    } catch (e) {
      return bad(500, `Server error: ${e.message}`)
    }
  },
}
