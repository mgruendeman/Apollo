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
    # a button for each mission with a review list (public/review/transcript/apolloNN.json)
    listed = sorted(int(p.stem.removeprefix('apollo')) for p in (OUT / 'transcript').glob('apollo*.json'))
    buttons = ' '.join(f'<button data-m="{n:02d}" aria-pressed="{str(k == 0).lower()}">Apollo {n}</button>' for k, n in enumerate(listed))
    (OUT / 'transcript.html').write_text(TRANSCRIPT.replace('__MISSION_BUTTONS__', buttons))
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
.from { font-size:.75rem; padding:1px 8px; border-radius:999px; border:1px solid var(--rule); }
.from.public { border-color:var(--accent); color:var(--accent); }
.actions .go { border-color:var(--good); color:var(--good); }
a { color:var(--accent); }
</style>
<main>
  <p><a href="./">← Photo review</a></p>
  <h1>Problem reports</h1>
  <p class="meta">Reports you send while signed in go straight to Claude's fix list. Visitors' reports wait here until you send them on.</p>
  <div class="bar" role="group" aria-label="Show">
    <button data-s="pending" aria-pressed="true">Waiting for you<span id="waiting"></span></button><button data-s="new" aria-pressed="false">With Claude</button>
    <button data-s="fixed" aria-pressed="false">Fixed</button><button data-s="dismissed" aria-pressed="false">Dismissed</button><button data-s="all" aria-pressed="false">All</button>
  </div>
  <div id="list"></div>
</main>
<script>
let status = 'pending'
const list = document.getElementById('list')
const LABEL = { pending: 'waiting for you', new: 'with Claude', fixed: 'fixed', dismissed: 'dismissed' }
// what can be done with a report in each state
const MOVES = {
  pending: [['new', 'Send to Claude', 'go'], ['dismissed', 'Dismiss']],
  new: [['fixed', 'Mark fixed'], ['dismissed', 'Dismiss'], ['pending', 'Back to waiting']],
  fixed: [['new', 'Reopen']],
  dismissed: [['pending', 'Back to waiting'], ['new', 'Send to Claude', 'go']],
}
const from = (x) => x.source === 'public' ? '<span class="from public">from a visitor</span>' : x.source === 'reviewer' ? '<span class="from">from you</span>' : ''
async function countWaiting() {
  const r = await fetch('/api/review/reports?status=pending')
  if (!r.ok) return
  const n = (await r.json()).reports.length
  document.getElementById('waiting').textContent = n ? ` (${n})` : ''
}
const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
async function load() {
  const r = await fetch('/api/review/reports?status=' + status)
  if (r.status === 401) { location.href = './'; return }
  const { reports } = await r.json()
  list.innerHTML = reports.length ? reports.map((x) => `<article>
      <div class="meta">#${x.id} · ${new Date(x.at).toLocaleString()} · ${esc(LABEL[x.status] || x.status)} ${from(x)}${x.contact ? ' · contact: ' + esc(x.contact) : ''}</div>
      <strong>${esc(x.subject)}</strong>
      <p class="msg">${esc(x.message)}</p>
      ${x.context ? `<pre>${esc(x.context)}</pre>` : ''}
      ${x.page ? `<div class="meta"><a href="${esc(x.page)}" target="_blank" rel="noreferrer">Page it was sent from ↗</a></div>` : ''}
      <div class="actions">${(MOVES[x.status] || []).map(([to, label, cls]) => `<button data-id="${x.id}" data-to="${to}"${cls ? ` class="${cls}"` : ''}>${label}</button>`).join('')}</div>
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
  countWaiting()
})
load()
countWaiting()
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
.tape { margin:4px 0 0; color:var(--muted); font-size:.8rem; overflow-wrap:anywhere; }
/* the page's row: wider than the screen on a phone and scrolled sideways, so the typing is legible; a tap enlarges it */
.rowwrap { overflow-x:auto; -webkit-overflow-scrolling:touch; margin:6px 0 0; border:1px solid var(--rule); border-radius:4px; background:#fff; }
img.row { display:block; width:max(100%, 760px); height:auto; }
.suggest { margin:6px 0 0; font-size:.93rem; overflow-wrap:anywhere; }
.suggest mark { background:#fde9b8; padding:0 2px; border-radius:2px; }
.suggest .accept { margin-left:6px; }
img.row { cursor: zoom-in; }
body.one .intro { display:none; }   /* (one at a time: the line itself at the top of the screen) */
body.one .line.is-main .text { font-size:1.05rem; }
body.one .line.is-main img.row { margin:10px 0; }
body.one .line.is-main .actions button { padding:8px 12px; font-size:1rem; }
body.one .suggest .accept { padding:8px 12px; font-size:1rem; }
.nav { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:6px 0; }
.nav button { padding:8px 14px; font-size:1rem; }
#zoom { position:fixed; inset:0; background:#111; z-index:50; overflow:hidden; touch-action:none; }
#zoom img { position:absolute; left:0; top:40%; width:100%; transform-origin:0 0; user-select:none; -webkit-user-drag:none; }
#zoom .close { position:absolute; top:12px; right:12px; z-index:2; padding:8px 14px; font-size:1rem; }
#zoom .hint { position:absolute; bottom:12px; left:0; right:0; text-align:center; color:#bbb; font-size:.85rem; margin:0; pointer-events:none; }
a { color:var(--accent); }
.empty { color:var(--muted); }
.actions { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
button { font:inherit; }
.actions button, .fix button, .more, #next, #aside { padding:2px 10px; border:1px solid var(--rule); border-radius:999px; background:var(--surface); color:var(--ink); cursor:pointer; font-size:.85rem; }
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
  <p class="intro">Lines that look doubtful — damaged words, a speaker or time the scan lost, or words the tape hears differently — each shown with the lines around it, since mistakes come in clusters. Under each listed line: what the tape says over it, the row as NASA typed it on the scanned page, and where the tape's words mend a damaged word, a suggested reading to Accept with one tap. Press ▶ to hear a line (all of it, from a few seconds before; as often as you like) and Report to say what it should be. A line you've reported is put aside here straight away, and leaves the list at the next run.</p>
  <audio id="player" preload="none"></audio>
  <div class="bar">
    <span role="group" aria-label="Mission">__MISSION_BUTTONS__</span>
    <span class="gap"></span>
    <span role="group" aria-label="Order"><button data-order="rank" aria-pressed="true">Most doubtful first</button> <button data-order="time" aria-pressed="false">In mission order</button></span>
    <span class="gap"></span>
    <span role="group" aria-label="View"><button data-mode="list" aria-pressed="true">As a list</button> <button data-mode="one" aria-pressed="false">One at a time</button></span>
  </div>
  <div id="list"></div>
  <div id="zoom" hidden><img alt="The row on NASA's page, enlarged"><button class="close">Close</button><p class="hint">Pinch to zoom, drag to move, double-tap to reset</p></div>
</main>
<script>
const PAGE = 100, AROUND = 2
let mission = (document.querySelector('[data-m][aria-pressed=true]') || { dataset: { m: '11' } }).dataset.m, order = 'rank', shown = PAGE
let mode = 'list', at = 0   // the view, and in the one-at-a-time view which of the lines to check is up
try { mode = localStorage.getItem('review-mode') === 'one' ? 'one' : 'list' } catch {}
if (/\bone\b/.test(location.hash)) mode = 'one'   // (a bookmark straight into the one-at-a-time view)
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
  if (!s || g > s.get + (s.to - s.from) * s.rate) return null
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

// how long a line takes to say, roughly (as the site's lineReport.js): to play all of it
const sayingSeconds = (t) => 2 + (t.match(/[A-Za-z]/g) || []).length * 0.09 + (t.match(/\d/g) || []).length * 1.0 + (t.match(/\*\*\*|\.\.\./g) || []).length * 3
function lineLength(k) {
  const l = lines[k], next = lines[k + 1]
  let length = sayingSeconds(l.t)
  if (next && next.g > l.g + length && next.g < l.g + 2 * length + 10) length = next.g - l.g
  return Math.min(360, Math.max(10, length + 1.5))
}
// The suggested line with the words it changes marked
function suggestHtml(from, to) {
  const was = new Set(from.split(' '))
  return to.split(' ').map((w) => (was.has(w) ? esc(w) : `<mark>${esc(w)}</mark>`)).join(' ')
}

function lineHtml(k, main, x) {
  const l = lines[k], a = audioFor(l.g)
  // for the listed line itself: what the tape says over it, NASA's typed row from the scanned page, and a
  // suggested reading from the tape's words to accept with one tap
  const help = main && x ? [
    x.asTyped ? `<p class="suggest">The model reads this line as NASA typed it (${Math.round(x.asTyped * 100)}% sure).</p>` : '',
    x.tape ? `<p class="tape">Tape: ${esc(x.tape.length > 420 ? x.tape.slice(0, 420) + '…' : x.tape)}</p>` : '',
    x.pg != null ? `<div class="rowwrap"><img class="row" loading="lazy" alt="This row on NASA's page" src="/api/review/media/review/pages/${mission}/${x.pg}-${x.pr}.jpg" onerror="this.parentNode.remove()"></div>` : '',
    x.suggest === '' ? `<p class="suggest">Suggested: nothing is said here, the row is scan scraps. <button class="accept" data-i="${rows.indexOf(x)}">Remove</button>${x.by === 'model' ? ' <span class="meta">(model' + (x.conf != null ? ', ' + Math.round(x.conf * 100) + '% sure' : '') + ')</span>' : ''}</p>`
    : x.suggest ? `<p class="suggest">Suggested: ${suggestHtml(l.t, x.suggest)} <button class="accept" data-i="${rows.indexOf(x)}">Accept</button>${x.by === 'model' ? ' <span class="meta">(model' + (x.conf != null ? ', ' + Math.round(x.conf * 100) + '% sure' : '') + ')</span>' : ''}</p>` : '',
  ].join('') : ''
  return `<div class="line${main ? ' is-main' : ''}${l.c ? ' is-pao' : ''}" data-k="${k}">
    <div class="top"><span class="meta"><a href="/#/mission/${mission}?at=${Math.floor(l.g)}" target="_blank" rel="noreferrer">${fmt(l.g)}</a> · ${esc(l.c ? 'Announcer' : l.s)}${l.n ? ' · not on this recording' : ''}</span>
    <span class="actions">${reported.has(keyOf(l)) ? '<span class="done">✓ reported</span>' : ''}${a ? `<button class="play" data-src="${esc(a.src)}" data-at="${a.at}" data-until="${Math.round((a.at + lineLength(k)) * 10) / 10}">▶ Play</button>` : '<span class="meta">no tape here</span>'}<button class="good" title="Checked against the tape: right as it is">✓ Correct</button><button class="report">Report a fix</button></span></div>
    <p class="text">${esc(l.t)}</p>${help}
  </div>`
}

function cardHtml(i) {
  const x = rows[i], r = around.get(i) || (mode === 'one' ? 1 : AROUND)
  const lo = Math.max(0, x.k - r), hi = Math.min(lines.length - 1, x.k + r)
  let body = ''
  for (let k = lo; k <= hi; k++) body += lineHtml(k, k === x.k, x)
  return `<article data-i="${i}"><div class="head"><span class="q">${x.q}</span><span class="why">${esc(x.why)}</span></div>${body}<button class="more">More around it</button></article>`
}

// Lines already reported from this device wait for the next rebuild of the list: put aside meanwhile.
let showReported = false
const isReported = (i) => reported.has(keyOf(lines[rows[i].k] || rows[i]))
function toCheck() {
  const all = rows.map((_, i) => i)
  const idx = showReported ? all : all.filter((i) => !isReported(i))
  if (order === 'time') idx.sort((a, b) => rows[a].g - rows[b].g)
  else idx.sort((a, b) => (rows[a].asTyped ? 1 : 0) - (rows[b].asTyped ? 1 : 0))   // (lines the model reads as typed go last; the sort is stable)
  return idx
}

function render() {
  document.querySelectorAll('[data-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.mode === mode)))
  document.body.classList.toggle('one', mode === 'one')
  if (!rows.length) { list.innerHTML = '<p class="empty">Nothing left to check.</p>'; return }
  const mine = rows.map((_, i) => i).filter(isReported).length
  const idx = toCheck()
  const aside = mine ? ` · ${mine} you've reported ${showReported ? 'shown' : 'put aside'} <button id="aside">${showReported ? 'Put them aside' : 'Show them'}</button>` : ''
  if (mode === 'one') {
    // one line per screen: the page's row at full width, the buttons under your thumb, Next to move on
    if (!idx.length) { list.innerHTML = `<p class="empty">Nothing left to check.${aside}</p>`; return }
    at = Math.min(Math.max(0, at), idx.length - 1)
    const nav = `<div class="nav"><button class="prev" ${at ? '' : 'disabled'}>‹ Previous</button><span class="meta">${at + 1} of ${idx.length}</span><button class="next" ${at < idx.length - 1 ? '' : 'disabled'}>Next ›</button></div>`
    list.innerHTML = nav + cardHtml(idx[at]) + nav + (aside ? `<p class="meta">${aside.slice(3)}</p>` : '')
    window.scrollTo(0, 0)
    return
  }
  list.innerHTML = `<p class="meta">${idx.length} lines to check${order === 'time' ? ', in mission order' : ', most doubtful first'}${aside}</p>`
    + (idx.length ? idx.slice(0, shown).map(cardHtml).join('') : '<p class="empty">Nothing left to check.</p>')
    + (shown < idx.length ? `<button id="next">Show ${Math.min(PAGE, idx.length - shown)} more</button>` : '')
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
    stopAt = Number(play.dataset.until) || at + 9   // (the whole line)
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
    line.insertAdjacentHTML('beforeend', `<form class="fix"><textarea rows="3" placeholder="What should it say? e.g. 'Houston, not Horton'; 'this is Bean'; 'the last word is time'"></textarea><div class="actions"><button type="submit">Send</button><button type="button" class="copy">Copy the line to edit</button><button type="button" class="cancel">Cancel</button><span class="meta status"></span></div></form>`)
    line.querySelector('textarea').focus()
    return
  }
  const cancel = e.target.closest('button.cancel')
  if (cancel) { cancel.closest('form').remove(); return }
  const copy = e.target.closest('button.copy')
  if (copy) {
    const box = copy.closest('form').querySelector('textarea')
    box.value = lines[Number(copy.closest('.line').dataset.k)].t
    box.focus()
    return
  }
  const good = e.target.closest('button.good')
  if (good) { send(good.closest('.line'), CORRECT, null); return }
  const accept = e.target.closest('button.accept')
  if (accept) { const sg = rows[Number(accept.dataset.i)].suggest; send(accept.closest('.line'), sg === '' ? 'Remove: scan scraps, nothing said here.' : sg, null); return }
  const more = e.target.closest('button.more')
  if (more) {
    const card = more.closest('article'), i = Number(card.dataset.i)
    around.set(i, (around.get(i) || AROUND) + 3)
    card.outerHTML = cardHtml(i)
    return
  }
  if (e.target.id === 'next') { shown += PAGE; render() }
  if (e.target.id === 'aside') { showReported = !showReported; render() }
})

// what "✓ Correct" sends (the site's report dialog sends the same)
const CORRECT = '✓ Correct as it is: mark complete, no changes.'

list.addEventListener('submit', async (e) => {
  e.preventDefault()
  const f = e.target
  const msg = f.querySelector('textarea').value.trim()
  if (msg) send(f.closest('.line'), msg, f)
})

async function send(line, msg, f) {
  const card = line.closest('article')
  const k = Number(line.dataset.k), l = lines[k], x = rows[Number(card.dataset.i)]
  const a = audioFor(l.g), status = f ? f.querySelector('.status') : { set textContent(v) {} }
  status.textContent = 'Sending…'
  const r = await fetch('/api/reports', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
    subject: `Apollo ${mission} GET ${fmt(l.g)}: transcript line`,
    message: msg,
    context: `${l.c ? 'Announcer' : l.s}: "${l.t}"\nGET ${fmt(l.g)}, in the whole-mission recording\nAudio: ${a ? a.src + ' at ' + a.at + ' s' : ''}\n`
      + (k === x.k ? `From the review list: ${x.why}` : `Near a line from the review list (GET ${fmt(x.g)})`),
    page: location.href }) })
  status.textContent = r.ok ? 'Sent.' : 'Could not send.'
  if (!r.ok) { if (!f) alert('Could not send that. Try again in a moment.'); return }
  reported.add(keyOf(l)); saveReported()
  const done = msg === CORRECT ? '✓ correct' : '✓ reported'
  setTimeout(() => {
    if (f) f.remove()
    document.querySelectorAll(`.line[data-k="${k}"] .top > .actions`).forEach((el) => { if (!el.querySelector('.done')) el.insertAdjacentHTML('afterbegin', `<span class="done">${done}</span>`) })
    // (one at a time: the line you've dealt with leaves the list, so the next one takes its place)
    if (mode === 'one' && k === x.k && !showReported) setTimeout(render, 500)
  }, f ? 700 : 0)
}

document.querySelector('.bar').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return
  if (b.dataset.m) {
    mission = b.dataset.m
    document.querySelectorAll('[data-m]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
    load()
  } else if (b.dataset.order) {
    order = b.dataset.order; shown = PAGE; at = 0
    document.querySelectorAll('[data-order]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
    render()
  } else if (b.dataset.mode) {
    mode = b.dataset.mode; at = 0
    try { localStorage.setItem('review-mode', mode) } catch {}
    render()
  }
})

list.addEventListener('click', (e) => {
  if (e.target.closest('button.prev')) { at -= 1; render() }
  else if (e.target.closest('button.next')) { at += 1; render() }
  else if (e.target.closest('img.row')) openZoom(e.target.closest('img.row').src)
})

// The page's row, enlarged: pinch to zoom, drag to move, double-tap to reset.
const zoom = document.getElementById('zoom'), zimg = zoom.querySelector('img')
let z = { scale: 1, x: 0, y: 0 }, pointers = new Map(), pinch = null, lastTap = 0
function place() { zimg.style.transform = `translate(${z.x}px, ${z.y}px) scale(${z.scale})` }
function openZoom(src) {
  zimg.src = src; z = { scale: 1, x: 0, y: 0 }; place()
  zoom.hidden = false; document.body.style.overflow = 'hidden'
}
function closeZoom() { zoom.hidden = true; document.body.style.overflow = '' }
zoom.querySelector('.close').addEventListener('click', closeZoom)
zoom.addEventListener('pointerdown', (e) => {
  if (e.target.closest('button')) return
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY })
  zoom.setPointerCapture(e.pointerId)
  if (pointers.size === 2) {
    const [a, b] = [...pointers.values()]
    pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), scale: z.scale, cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2, x: z.x, y: z.y }
  } else if (pointers.size === 1) {
    const now = Date.now()
    if (now - lastTap < 300) { z = z.scale > 1 ? { scale: 1, x: 0, y: 0 } : { scale: 2.5, x: -(e.clientX - zoom.clientWidth / 2) * 1.5, y: -(e.clientY - zoom.clientHeight / 2) * 1.5 }; place() }
    lastTap = now
  }
})
zoom.addEventListener('pointermove', (e) => {
  if (!pointers.has(e.pointerId)) return
  const was = pointers.get(e.pointerId)
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY })
  if (pointers.size === 2 && pinch) {
    const [a, b] = [...pointers.values()]
    const k = Math.hypot(a.x - b.x, a.y - b.y) / pinch.d
    const scale = Math.min(6, Math.max(1, pinch.scale * k))
    const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2
    // zoom about the pinch's centre, and follow it as it moves
    z = { scale, x: cx - (pinch.cx - pinch.x) * (scale / pinch.scale), y: cy - (pinch.cy - pinch.y) * (scale / pinch.scale) }
    place()
  } else if (pointers.size === 1) {
    z.x += e.clientX - was.x; z.y += e.clientY - was.y; place()
  }
})
const lift = (e) => { pointers.delete(e.pointerId); if (pointers.size < 2) pinch = null }
zoom.addEventListener('pointerup', lift); zoom.addEventListener('pointercancel', lift)
load()
</script>
"""

if __name__ == '__main__':
    main()
