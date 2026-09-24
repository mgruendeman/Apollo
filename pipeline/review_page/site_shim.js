// On the site, the review page keeps its marks in our own database
// (worker/index.js, /api/review/...) instead of claude.ai's artifact store.
// This shim gives script.js the same small interface it uses there
// (claude.use('db') / claude.use('user')), plus a password sign-in.
(() => {
  const API = '/api/review'
  const api = (path, opts = {}) =>
    fetch(API + path, { credentials: 'same-origin', ...opts, headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) } })

  function signIn() {
    const box = document.createElement('div')
    box.className = 'signin'
    box.innerHTML = `<form><h2>Photo review</h2><p>Enter the review password.</p>
      <input type="password" id="review-password" autocomplete="current-password" aria-label="Password" required>
      <button type="submit">Sign in</button><p class="signin-error" role="alert"></p></form>`
    document.body.appendChild(box)
    const form = box.querySelector('form')
    box.querySelector('input').focus()
    form.addEventListener('submit', async (e) => {
      e.preventDefault()
      const r = await api('/login', { method: 'POST', body: JSON.stringify({ password: box.querySelector('input').value }) })
      if (r.ok) location.reload()
      else box.querySelector('.signin-error').textContent = (await r.json().catch(() => ({}))).error || 'Sign-in failed.'
    })
  }

  const db = {
    collection(name) {
      if (name !== 'reviews') throw new Error('only reviews')
      return {
        doc: (id) => ({
          set: async (body) => {
            const r = await api(`/marks/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(body) })
            if (!r.ok) throw { code: r.status === 401 ? 'invalid_argument' : 'unavailable' }
          },
          delete: async () => {
            const r = await api(`/marks/${encodeURIComponent(id)}`, { method: 'DELETE' })
            if (!r.ok) throw { code: 'unavailable' }
          },
        }),
        // Polls every 20 s (and when the tab comes back) and reports what changed.
        onSnapshot(next, onError) {
          let known = new Map()
          let stopped = false
          async function poll() {
            if (stopped) return
            try {
              const r = await api('/marks')
              if (r.status === 401) { onError && onError({ code: 'revoked' }); return }
              const { reviews } = await r.json()
              const now = new Map(reviews.map((d) => [d.id, d]))
              const changes = []
              for (const [id, d] of now) {
                const old = known.get(id)
                if (!old || old.updated !== d.updated) changes.push({ type: old ? 'modified' : 'added', doc: { id, exists: true, data: () => d.data } })
              }
              for (const [id, d] of known) if (!now.has(id)) changes.push({ type: 'removed', doc: { id, exists: true, data: () => d.data } })
              known = now
              if (changes.length) next({ docChanges: () => changes })
            } catch { /* try again next time */ }
          }
          poll()
          const t = setInterval(poll, 20000)
          const vis = () => document.visibilityState === 'visible' && poll()
          document.addEventListener('visibilitychange', vis)
          return () => { stopped = true; clearInterval(t); document.removeEventListener('visibilitychange', vis) }
        },
      }
    },
  }
  const user = {
    id: async () => 'reviewer',
    can: async () => true,
    profiles: async (ids) => Object.fromEntries([].concat(ids).map((i) => [i, { id: i, name: i === 'reviewer' ? 'you' : 'a reviewer' }])),
  }

  let signedIn = null
  window.claude = {
    use: async (name) => {
      signedIn ??= api('/me').then((r) => r.ok)
      if (!(await signedIn)) {
        if (name === 'db') signIn()
        return null
      }
      return name === 'db' ? db : name === 'user' ? user : null
    },
  }
})()
