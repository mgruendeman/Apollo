"""Build the reviewer pages for the site (public/review/).

  public/review/index.html    the photo review editor, listing every frame
                              with a cleaned photo on R2 (from the
                              photo-index/*.cleaned.json lists that
                              upload_photos.py writes)
  public/review/reports.html  problem reports sent from the site
  public/review/transcript.html  the lines of each mission's transcript most
                              worth a listener's ear, ranked (align_tapes.py
                              writes public/review/transcript/apolloNN.json)

Both are behind the reviewer password (worker/index.js); the editor loads
the cleaned photos through the Worker so its live preview can read them.
upload_photos.py runs this after each upload.

    python pipeline/review_page/build_site.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
INDEX = ROOT / 'public' / 'photo-index'
OUT = ROOT / 'public' / 'review'
ASU = 'https://tothemoon.im-ldi.com'
DIALS = ('brightness', 'contrast', 'shadows', 'highlights', 'warmth', 'tint', 'saturation', 'straighten', 'rotate')


def scan_url(fid, fmt):
    roll = fid[:4].upper()
    return f'{ASU}/data_a/{roll}/png/{fid}_SML.png' if fmt == 'b' else f'{ASU}/data_a70/{roll}/extra/{fid}.small.png'


def main():
    reviews = json.loads((HERE.parent / 'photo_reviews.json').read_text())
    frames = []
    for lst in sorted(INDEX.glob('*.cleaned.json')):
        mission = lst.name[:2]
        rows = {r[0]: r for r in json.loads((INDEX / f'{mission}.json').read_text())['frames']}
        for fid in json.loads(lst.read_text())['cleaned']:
            row = rows.get(fid, [fid, 'a', '', None, ''])
            media = f'/api/review/media/photos/{mission}/{fid}'
            # The photo on R2 was made with the marks it had at the last processing run.
            marks = reviews.get(fid, {})
            frames.append({'id': fid, 'mission': str(int(mission)), 'caption': row[4] or '',
                           'ours': f'{media}.jpg', 'thumb': f'{media}.thumb.jpg', 'raw': scan_url(fid, row[1]), 'nasa': None,
                           'rendered': {k: marks[k] for k in DIALS if marks.get(k)}})
    script = (HERE / 'script.js').read_text().replace('__FRAMES__', json.dumps(frames, separators=(',', ':')))
    page = (HERE / 'template.html').read_text()
    page = page.replace('__SCRIPT__', (HERE / 'site_shim.js').read_text() + '\n' + script)
    page = page.replace("Reviews can't be saved in this view. Open the page in Claude to review.", 'Sign in to review.')
    page = page.replace('<nav class="strip"', '<p class="notice" style="background:none;padding:4px 16px"><a href="reports.html">Problem reports →</a> · <a href="transcript.html">Transcript lines to check →</a></p>\n  <nav class="strip"', 1)
    page = page.replace('</style>', SIGNIN_CSS + '</style>', 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="robots" content="noindex">\n' + page)
    (OUT / 'reports.html').write_text(REPORTS)
    (OUT / 'transcript.html').write_text(TRANSCRIPT)
    print(f'wrote {OUT}/index.html ({len(frames)} photos), reports.html and transcript.html')


SIGNIN_CSS = """
.signin { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; background: var(--ground); padding: 16px; }
.signin form { display: grid; gap: 10px; width: min(100%, 340px); background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 20px; }
.signin h2 { margin: 0; font-size: 1.2rem; }
.signin p { margin: 0; color: var(--muted); font-size: .9rem; }
.signin input { font: 1rem var(--sans); padding: 8px 10px; border: 1px solid var(--rule); border-radius: 6px; background: var(--ground); color: var(--ink); }
.signin button { font: 600 1rem var(--sans); padding: 9px; border: 0; border-radius: 6px; background: var(--accent); color: var(--accent-ink); cursor: pointer; }
.signin .signin-error { color: var(--flag); min-height: 1.2em; }
"""

REPORTS = r"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Problem Reports</title>
<style>
:root { --ground:#eef1ee; --surface:#fff; --ink:#1b2320; --muted:#5d6a65; --rule:#d3dad6; --accent:#b8741a; --good:#2f7d4f; color-scheme: light; }
@media (prefers-color-scheme: dark) { :root { --ground:#101513; --surface:#182019; --ink:#e3eae5; --muted:#98a69f; --rule:#2c3830; --accent:#e3a444; --good:#6cc48f; color-scheme: dark; } }
body { margin:0; background:var(--ground); color:var(--ink); font:15px/1.5 system-ui, sans-serif; padding:20px 16px 40px; }
main { max-width:860px; margin:0 auto; display:grid; gap:14px; }
h1 { margin:0; font-size:1.5rem; }
.bar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.bar button, .actions button { font:inherit; padding:5px 12px; border:1px solid var(--rule); border-radius:999px; background:var(--surface); color:var(--ink); cursor:pointer; }
.bar button[aria-pressed=true] { background:var(--ink); color:var(--ground); }
article { background:var(--surface); border:1px solid var(--rule); border-radius:10px; padding:14px; display:grid; gap:6px; }
.meta { color:var(--muted); font-size:.82rem; }
.msg { white-space:pre-wrap; margin:0; }
pre { margin:0; white-space:pre-wrap; font-size:.8rem; color:var(--muted); background:var(--ground); padding:8px; border-radius:6px; }
.actions { display:flex; gap:8px; }
.empty { color:var(--muted); }
a { color:var(--accent); }
</style>
<main>
  <p><a href="./">← Photo review</a></p>
  <h1>Problem reports</h1>
  <div class="bar" role="group" aria-label="Show">
    <button data-s="new" aria-pressed="true">New</button><button data-s="fixed" aria-pressed="false">Fixed</button>
    <button data-s="dismissed" aria-pressed="false">Dismissed</button><button data-s="all" aria-pressed="false">All</button>
  </div>
  <div id="list"></div>
</main>
<script>
let status = 'new'
const list = document.getElementById('list')
const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
async function load() {
  const r = await fetch('/api/review/reports?status=' + status)
  if (r.status === 401) { location.href = './'; return }
  const { reports } = await r.json()
  list.innerHTML = reports.length ? reports.map((x) => `<article>
      <div class="meta">#${x.id} · ${new Date(x.at).toLocaleString()} · ${esc(x.status)}${x.contact ? ' · contact: ' + esc(x.contact) : ''}</div>
      <strong>${esc(x.subject)}</strong>
      <p class="msg">${esc(x.message)}</p>
      ${x.context ? `<pre>${esc(x.context)}</pre>` : ''}
      ${x.page ? `<div class="meta"><a href="${esc(x.page)}" target="_blank" rel="noreferrer">Page it was sent from ↗</a></div>` : ''}
      <div class="actions">${['fixed', 'dismissed', 'new'].filter((s) => s !== x.status).map((s) => `<button data-id="${x.id}" data-to="${s}">Mark ${s}</button>`).join('')}</div>
    </article>`).join('') : '<p class="empty">Nothing here.</p>'
}
document.querySelector('.bar').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return
  status = b.dataset.s
  document.querySelectorAll('.bar button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
  load()
})
list.addEventListener('click', async (e) => {
  const b = e.target.closest('button[data-to]'); if (!b) return
  await fetch('/api/review/reports/' + b.dataset.id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: b.dataset.to }) })
  load()
})
load()
</script>
"""

TRANSCRIPT = r"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Transcript lines to check</title>
<style>
:root { --ground:#eef1ee; --surface:#fff; --ink:#1b2320; --muted:#5d6a65; --rule:#d3dad6; --accent:#b8741a; --main:#fbf1e3; --ok:#2e7d4f; color-scheme: light; }
@media (prefers-color-scheme: dark) { :root { --ground:#101513; --surface:#182019; --ink:#e3eae5; --muted:#98a69f; --rule:#2c3830; --accent:#e3a444; --main:#2a241a; --ok:#6fcf97; color-scheme: dark; } }
body { margin:0; background:var(--ground); color:var(--ink); font:15px/1.5 system-ui, sans-serif; padding:20px 16px 40px; }
main { max-width:860px; margin:0 auto; display:grid; gap:12px; }
h1 { margin:0; font-size:1.5rem; }
.bar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.bar button { font:inherit; padding:5px 12px; border:1px solid var(--rule); border-radius:999px; background:var(--surface); color:var(--ink); cursor:pointer; }
.bar button[aria-pressed=true] { background:var(--ink); color:var(--ground); }
.bar .gap { width:12px; }
.intro, .meta, .why { color:var(--muted); font-size:.85rem; }
#list { display:grid; gap:12px; }
article { background:var(--surface); border:1px solid var(--rule); border-radius:10px; padding:10px 10px 8px; display:grid; gap:2px; }
.head { display:flex; gap:10px; align-items:baseline; padding:0 4px 4px; }
.q { font-variant-numeric:tabular-nums; color:var(--accent); font-weight:600; }
.line { display:grid; gap:1px; padding:5px 8px 6px 10px; border-left:3px solid transparent; border-radius:6px; }
.top { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:2px 10px; }
.line.is-main { border-left-color:var(--accent); background:var(--main); }
.line:not(.is-main) .text { font-size:.93rem; }
.line.is-pao .text { color:var(--muted); font-style:italic; }
.text { margin:0; overflow-wrap:anywhere; }
a { color:var(--accent); }
.empty { color:var(--muted); }
.actions { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
button { font:inherit; }
.actions button, .fix button, .more, #next { padding:2px 10px; border:1px solid var(--rule); border-radius:999px; background:var(--surface); color:var(--ink); cursor:pointer; font-size:.85rem; }
button.play { border-color:var(--accent); color:var(--accent); }
.more { justify-self:start; margin:4px 0 0 10px; color:var(--muted); }
#next { justify-self:center; padding:6px 16px; }
.done { color:var(--ok); font-size:.85rem; }
.fix { display:grid; gap:6px; margin-top:4px; }
.fix textarea { font:inherit; padding:8px; border:1px solid var(--rule); border-radius:6px; background:var(--ground); color:var(--ink); resize:vertical; }
</style>
<main>
  <p><a href="./">← Photo review</a> · <a href="reports.html">Problem reports</a></p>
  <h1>Transcript lines to check</h1>
  <p class="intro">Lines that look doubtful — damaged words, a speaker or time the scan lost, or words the tape hears differently — each shown with the lines around it, since mistakes come in clusters. Press ▶ to hear a line (a few seconds either side, as often as you like) and Report to say what it should be. Fixed lines drop off at the next run.</p>
  <audio id="player" preload="none"></audio>
  <div class="bar">
    <span role="group" aria-label="Mission"><button data-m="11" aria-pressed="true">Apollo 11</button> <button data-m="12" aria-pressed="false">Apollo 12</button> <button data-m="14" aria-pressed="false">Apollo 14</button></span>
    <span class="gap"></span>
    <span role="group" aria-label="Order"><button data-order="rank" aria-pressed="true">Most doubtful first</button> <button data-order="time" aria-pressed="false">In mission order</button></span>
  </div>
  <div id="list"></div>
</main>
<script>
const PAGE = 100, AROUND = 2
let mission = '11', order = 'rank', shown = PAGE
let rows = [], lines = [], segs = [], gets = [], ext = null
const around = new Map()   // card -> lines shown either side
const list = document.getElementById('list')
const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
const fmt = (g) => { const t = Math.floor(Math.abs(g)); return (g < 0 ? '-' : '') + String(Math.floor(t / 3600)).padStart(3, '0') + ':' + String(Math.floor((t % 3600) / 60)).padStart(2, '0') + ':' + String(t % 60).padStart(2, '0') }
const keyOf = (l) => l.g + '|' + l.t

// lines reported from this page, remembered on this device until the text changes
let reported = new Set()
const store = () => 'apollo-review-reported-' + mission
function loadReported() { try { reported = new Set(JSON.parse(localStorage.getItem(store()) || '[]')) } catch { reported = new Set() } }
function saveReported() { try { localStorage.setItem(store(), JSON.stringify([...reported].slice(-2000))) } catch {} }

function bisectRight(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] <= x) lo = m + 1; else hi = m } return lo }
// the file and the second in it where mission time g plays (as the pipeline works it out)
function audioFor(g) {
  const s = segs[bisectRight(gets, g) - 1]
  if (!s || s.journal || g > s.get + (s.to - s.from) * s.rate) return null
  const src = ext ? `/api/review/media/audio/${Number(mission)}/${s.tape}${ext}` : `https://archive.org/download/Apollo${Number(mission)}Audio/${s.tape}.mp3`
  return { src, at: Math.round((s.from + (g - s.get) / s.rate) * 10) / 10 }
}

async function load() {
  list.innerHTML = '<p class="empty">Loading…</p>'
  const [r, t] = await Promise.all([fetch('transcript/apollo' + mission + '.json'), fetch('/timeline/apollo' + mission + '.json')])
  if (!r.ok) { list.innerHTML = '<p class="empty">No list for this mission yet.</p>'; return }
  rows = await r.json()
  const tl = t.ok ? await t.json() : { lines: [], segments: [] }
  lines = tl.lines; segs = tl.segments; gets = segs.map((s) => s.get); ext = tl.audio ? tl.audio.ext : null
  const index = new Map(lines.map((l, k) => [keyOf(l), k]))
  const lineGets = lines.map((l) => l.g)
  rows.forEach((x) => { x.k = index.has(keyOf(x)) ? index.get(keyOf(x)) : Math.max(0, bisectRight(lineGets, x.g) - 1) })
  around.clear(); shown = PAGE; loadReported()
  render()
}

function lineHtml(k, main) {
  const l = lines[k], a = audioFor(l.g)
  return `<div class="line${main ? ' is-main' : ''}${l.c ? ' is-pao' : ''}" data-k="${k}">
    <div class="top"><span class="meta"><a href="/#/mission/${mission}?at=${Math.floor(l.g)}" target="_blank" rel="noreferrer">${fmt(l.g)}</a> · ${esc(l.c ? 'Announcer' : l.s)}${l.n ? ' · not on this recording' : ''}</span>
    <span class="actions">${reported.has(keyOf(l)) ? '<span class="done">✓ reported</span>' : ''}${a ? `<button class="play" data-src="${esc(a.src)}" data-at="${a.at}">▶ Play</button>` : '<span class="meta">no tape here</span>'}<button class="report">Report a fix</button></span></div>
    <p class="text">${esc(l.t)}</p>
  </div>`
}

function cardHtml(i) {
  const x = rows[i], r = around.get(i) || AROUND
  const lo = Math.max(0, x.k - r), hi = Math.min(lines.length - 1, x.k + r)
  let body = ''
  for (let k = lo; k <= hi; k++) body += lineHtml(k, k === x.k)
  return `<article data-i="${i}"><div class="head"><span class="q">${x.q}</span><span class="why">${esc(x.why)}</span></div>${body}<button class="more">More around it</button></article>`
}

function render() {
  if (!rows.length) { list.innerHTML = '<p class="empty">Nothing left to check.</p>'; return }
  const idx = rows.map((_, i) => i)
  if (order === 'time') idx.sort((a, b) => rows[a].g - rows[b].g)
  list.innerHTML = `<p class="meta">${rows.length} lines to check${order === 'time' ? ', in mission order' : ', most doubtful first'}</p>`
    + idx.slice(0, shown).map(cardHtml).join('')
    + (shown < rows.length ? `<button id="next">Show ${Math.min(PAGE, rows.length - shown)} more</button>` : '')
}

const player = document.getElementById('player')
let stopAt = 0
player.addEventListener('timeupdate', () => { if (player.currentTime >= stopAt) player.pause() })
player.addEventListener('pause', () => document.querySelectorAll('button.play').forEach((b) => (b.textContent = '▶ Play')))

list.addEventListener('click', (e) => {
  const play = e.target.closest('button.play')
  if (play) {
    const same = player.dataset.src === play.dataset.src && Math.abs(player.dataset.at - play.dataset.at) < 1
    if (!player.paused && same) { player.pause(); return }
    player.pause()
    if (player.dataset.src !== play.dataset.src) { player.src = play.dataset.src; player.dataset.src = play.dataset.src }
    player.dataset.at = play.dataset.at
    const at = Number(play.dataset.at)
    stopAt = at + 9
    const start = () => { player.currentTime = Math.max(0, at - 3); player.play().catch(() => {}) }
    if (player.readyState >= 1) start(); else { player.addEventListener('loadedmetadata', start, { once: true }); player.load() }
    document.querySelectorAll('button.play').forEach((b) => (b.textContent = '▶ Play'))
    play.textContent = '❚❚ Stop'
    return
  }
  const rep = e.target.closest('button.report')
  if (rep) {
    const line = rep.closest('.line')
    let f = line.querySelector('form.fix')
    if (f) { f.remove(); return }
    line.insertAdjacentHTML('beforeend', `<form class="fix"><textarea rows="3" placeholder="What should it say? e.g. 'Houston, not Horton'; 'this is Bean'; 'the last word is time'"></textarea><div class="actions"><button type="submit">Send</button><button type="button" class="cancel">Cancel</button><span class="meta status"></span></div></form>`)
    line.querySelector('textarea').focus()
    return
  }
  const cancel = e.target.closest('button.cancel')
  if (cancel) { cancel.closest('form').remove(); return }
  const more = e.target.closest('button.more')
  if (more) {
    const card = more.closest('article'), i = Number(card.dataset.i)
    around.set(i, (around.get(i) || AROUND) + 3)
    card.outerHTML = cardHtml(i)
    return
  }
  if (e.target.id === 'next') { shown += PAGE; render() }
})

list.addEventListener('submit', async (e) => {
  e.preventDefault()
  const f = e.target, line = f.closest('.line'), card = f.closest('article')
  const k = Number(line.dataset.k), l = lines[k], x = rows[Number(card.dataset.i)]
  const msg = f.querySelector('textarea').value.trim()
  if (!msg) return
  const a = audioFor(l.g), status = f.querySelector('.status')
  status.textContent = 'Sending…'
  const r = await fetch('/api/reports', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
    subject: `Apollo ${mission} GET ${fmt(l.g)}: transcript line`,
    message: msg,
    context: `${l.c ? 'Announcer' : l.s}: "${l.t}"\nGET ${fmt(l.g)}, in the whole-mission recording\nAudio: ${a ? a.src + ' at ' + a.at + ' s' : ''}\n`
      + (k === x.k ? `From the review list: ${x.why}` : `Near a line from the review list (GET ${fmt(x.g)})`),
    page: location.href }) })
  status.textContent = r.ok ? 'Sent.' : 'Could not send.'
  if (!r.ok) return
  reported.add(keyOf(l)); saveReported()
  setTimeout(() => {
    f.remove()
    document.querySelectorAll(`.line[data-k="${k}"] .top > .actions`).forEach((el) => { if (!el.querySelector('.done')) el.insertAdjacentHTML('afterbegin', '<span class="done">✓ reported</span>') })
  }, 700)
})

document.querySelector('.bar').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return
  if (b.dataset.m) {
    mission = b.dataset.m
    document.querySelectorAll('[data-m]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
    load()
  } else if (b.dataset.order) {
    order = b.dataset.order; shown = PAGE
    document.querySelectorAll('[data-order]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
    render()
  }
})
load()
</script>
"""

if __name__ == '__main__':
    main()
