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
    page = page.replace('<nav class="strip"', '<p class="notice" style="background:none;padding:4px 16px"><a href="reports.html">Problem reports →</a> · <a href="transcript.html">Transcript lines to check →</a> · <a href="stats.html">Site statistics →</a></p>\n  <nav class="strip"', 1)
    page = page.replace('</style>', SIGNIN_CSS + '</style>', 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="robots" content="noindex">\n' + page)
    (OUT / 'reports.html').write_text(REPORTS)
    (OUT / 'stats.html').write_text(STATS)
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

STATS = r"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Site Statistics</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
:root { --ground:#eef1ee; --surface:#fff; --ink:#1b2320; --muted:#5d6a65; --rule:#d3dad6; --accent:#b8741a; --bar:#c9873a; --c2:#3f7f9a; --c3:#7a9a3f; --empty:#e6ebe7; color-scheme: light; }
@media (prefers-color-scheme: dark) { :root { --ground:#101513; --surface:#182019; --ink:#e3eae5; --muted:#98a69f; --rule:#2c3830; --accent:#e3a444; --bar:#e3a444; --c2:#6db3d1; --c3:#a9cc6a; --empty:#232d27; color-scheme: dark; } }
body { margin:0; background:var(--ground); color:var(--ink); font:15px/1.5 system-ui, sans-serif; padding:20px 16px 40px; }
main { max-width:1000px; margin:0 auto; display:grid; gap:14px; }
h1 { margin:0; font-size:1.5rem; } h2 { margin:0 0 8px; font-size:1.05rem; }
a { color:var(--accent); }
.bar { display:flex; flex-wrap:wrap; gap:8px; }
.bar button { font:inherit; padding:5px 12px; border:1px solid var(--rule); border-radius:999px; background:var(--surface); color:var(--ink); cursor:pointer; }
.bar button[aria-pressed=true] { background:var(--ink); color:var(--ground); }
.tiles { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px; }
.tile, section { background:var(--surface); border:1px solid var(--rule); border-radius:10px; padding:12px 14px; min-width:0; }
.tile b { display:block; font-size:1.6rem; line-height:1.2; } .tile span { color:var(--muted); font-size:.82rem; }
svg { display:block; width:100%; height:auto; overflow:visible; }
svg text { fill:var(--muted); font-size:11px; }
.axis line, .axis path { stroke:var(--rule); }
.legend { display:flex; gap:14px; flex-wrap:wrap; font-size:.82rem; color:var(--muted); margin-top:6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; vertical-align:-1px; }
table { width:100%; border-collapse:collapse; font-size:.9rem; }
td { padding:4px 0; border-bottom:1px solid var(--rule); vertical-align:middle; }
td.n { text-align:right; white-space:nowrap; padding-left:10px; font-variant-numeric:tabular-nums; }
td.w { width:38%; padding-left:10px; } td.w i { display:block; height:8px; background:var(--bar); border-radius:4px; }
.grid2 { display:grid; grid-template-columns:repeat(auto-fit, minmax(290px, 1fr)); gap:14px; }
.meta, .empty { color:var(--muted); font-size:.85rem; }
.thumbs { display:grid; grid-template-columns:repeat(auto-fill, minmax(110px, 1fr)); gap:10px; }
.thumbs button { all:unset; cursor:pointer; display:grid; gap:3px; font-size:.78rem; color:var(--muted); }
.thumbs img { width:100%; aspect-ratio:1; object-fit:cover; border-radius:6px; background:var(--empty); }
.thumbs b { color:var(--ink); }
#viewer { position:fixed; inset:0; background:rgba(0,0,0,.88); display:none; align-items:center; justify-content:center; flex-direction:column; gap:10px; z-index:9; padding:16px; }
#viewer img { max-width:100%; max-height:80vh; border-radius:6px; }
#viewer p { color:#ddd; margin:0; font-size:.9rem; text-align:center; } #viewer a { color:#e3a444; }
.tip { position:fixed; pointer-events:none; background:var(--ink); color:var(--ground); font-size:.8rem; padding:3px 7px; border-radius:4px; display:none; }
</style>
<main>
  <p><a href="./">← Photo review</a> · <a href="reports.html">Problem reports</a> · <a href="transcript.html">Transcript lines</a></p>
  <h1>Site statistics</h1>
  <p class="meta">Counted by the site itself: totals by day, with no cookies, no addresses and nothing that follows a visitor. A visitor is a device on a day; a person is a visitor who tapped, scrolled or pressed a key. Bots are counted apart: those that run the page by their name, and every page request (script or not) as browser or bot.</p>
  <div class="bar" role="group" aria-label="Period"><button data-d="7" aria-pressed="false">7 days</button><button data-d="30" aria-pressed="true">30 days</button><button data-d="90" aria-pressed="false">90 days</button><button data-d="365" aria-pressed="false">A year</button></div>
  <div class="tiles" id="tiles"></div>
  <section><h2>Visits a day</h2><div id="daily"></div><div class="legend"><span><i style="background:var(--c2)"></i>page views</span><span><i style="background:var(--bar)"></i>visitors</span><span><i style="background:var(--c3)"></i>people (did something)</span></div></section>
  <section><h2>Where visitors are</h2><div id="map"></div><p class="meta" id="mapnote"></p></section>
  <div class="grid2">
    <section><h2>How visitors arrived</h2><div id="kinds"></div><table id="sources"></table></section>
    <section><h2>People or bots</h2><div id="humans"></div><table id="bots"></table></section>
    <section><h2>Time of day (your time)</h2><div id="hours"></div></section>
    <section><h2>Tape listened a day</h2><div id="listenDaily"></div></section>
    <section><h2>Devices</h2><table id="devices"></table></section>
    <section><h2>Browsers</h2><table id="browsers"></table></section>
    <section><h2>Missions opened</h2><table id="missions"></table></section>
    <section><h2>Hours of tape listened</h2><table id="listened"></table></section>
    <section><h2>Highlights played</h2><table id="highlights"></table></section>
    <section><h2>Most-heard mission hours</h2><table id="mhours"></table></section>
    <section><h2>Pages</h2><table id="pages"></table></section>
    <section><h2>Countries</h2><table id="countries"></table></section>
    <section><h2>Reactions</h2><table id="reacts"></table></section>
    <section style="grid-column:1/-1"><h2>Photos opened</h2><div id="photos" class="thumbs"></div></section>
  </div>
</main>
<div class="tip" id="tip"></div>
<div id="viewer"><img alt=""><p></p></div>
<script>
let days = 30, world = null
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
const fmt = (n) => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k' : String(Math.round(n))
const mname = (m) => m ? 'Apollo ' + Number(m) : '(none)'
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim()
const tip = document.getElementById('tip')
const showTip = (e, text) => { tip.textContent = text; tip.style.display = 'block'; tip.style.left = e.clientX + 12 + 'px'; tip.style.top = e.clientY + 12 + 'px' }
const hideTip = () => { tip.style.display = 'none' }
let regionName = null
try { regionName = new Intl.DisplayNames(['en'], { type: 'region' }) } catch {}
const country = (c) => { try { return regionName ? regionName.of(c) : c } catch { return c } }
function sum(rows, kind, key) {
  const out = new Map()
  for (const r of rows) if (r.kind === kind) { const k = key(r); out.set(k, (out.get(k) || 0) + r.n) }
  return [...out.entries()].sort((a, b) => b[1] - a[1])
}
function table(id, entries, label = (k) => k, value = fmt, limit = 12) {
  const el = document.getElementById(id), top = entries.slice(0, limit), max = top.length ? top[0][1] : 1
  el.innerHTML = top.length ? top.map(([k, n]) => `<tr><td>${esc(label(k))}</td><td class="w"><i style="width:${Math.max(2, 100 * n / max)}%"></i></td><td class="n">${value(n)}</td></tr>`).join('')
    : '<tr><td class="empty">Nothing yet.</td></tr>'
}
// lines over the days: series [{name, color, values: Map(day -> n)}]
function lines(id, dayList, series, h = 190) {
  const el = document.getElementById(id), W = el.clientWidth || 600, m = { t: 8, r: 8, b: 22, l: 34 }
  const x = d3.scalePoint().domain(dayList).range([m.l, W - m.r])
  const max = d3.max(series, (s) => d3.max(dayList, (d) => s.values.get(d) || 0)) || 1
  const y = d3.scaleLinear().domain([0, max]).nice().range([h - m.b, m.t])
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${h}`)
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`)
    .call(d3.axisBottom(x).tickValues(dayList.filter((_, i) => i % Math.ceil(dayList.length / 7) === 0)).tickFormat((d) => d.slice(5)))
  svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat(fmt))
  for (const s of series) {
    svg.append('path').attr('fill', 'none').attr('stroke', css(s.color)).attr('stroke-width', 2)
      .attr('d', d3.line().x((d) => x(d)).y((d) => y(s.values.get(d) || 0))(dayList))
    svg.selectAll(null).data(dayList).join('circle').attr('cx', (d) => x(d)).attr('cy', (d) => y(s.values.get(d) || 0)).attr('r', 3).attr('fill', css(s.color))
      .on('mousemove', (e, d) => showTip(e, `${d}: ${s.values.get(d) || 0} ${s.name}`)).on('mouseleave', hideTip)
  }
  el.replaceChildren(svg.node())
}
function bars(id, labels, values, color = '--bar', h = 160, fmtTip = (l, v) => `${l}: ${v}`) {
  const el = document.getElementById(id), W = el.clientWidth || 600, m = { t: 8, r: 6, b: 22, l: 34 }
  const x = d3.scaleBand().domain(labels).range([m.l, W - m.r]).padding(0.15)
  const y = d3.scaleLinear().domain([0, d3.max(values) || 1]).nice().range([h - m.b, m.t])
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${h}`)
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`)
    .call(d3.axisBottom(x).tickValues(labels.filter((_, i) => i % Math.ceil(labels.length / Math.max(4, Math.min(12, W / 55))) === 0)))
  svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat(fmt))
  svg.selectAll(null).data(labels).join('rect').attr('x', (d) => x(d)).attr('width', x.bandwidth())
    .attr('y', (d, i) => y(values[i])).attr('height', (d, i) => y(0) - y(values[i])).attr('fill', css(color)).attr('rx', 2)
    .on('mousemove', (e, d) => showTip(e, fmtTip(d, values[labels.indexOf(d)]))).on('mouseleave', hideTip)
  el.replaceChildren(svg.node())
}
function split(id, parts) {   // one bar split by share: [[label, n, color]]
  const total = parts.reduce((a, p) => a + p[1], 0) || 1
  document.getElementById(id).innerHTML = `<div style="display:flex;height:16px;border-radius:5px;overflow:hidden;margin-bottom:6px">${
    parts.map(([l, n, c]) => n ? `<div title="${esc(l)}: ${n}" style="width:${100 * n / total}%;background:var(${c})"></div>` : '').join('')}</div>
    <div class="legend">${parts.map(([l, n, c]) => `<span><i style="background:var(${c})"></i>${esc(l)} ${Math.round(100 * n / total)}% (${fmt(n)})</span>`).join('')}</div>`
}
async function drawMap(byCountry) {
  const el = document.getElementById('map')
  if (!world) {
    try { world = await (await fetch('https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@v5.1.2/geojson/ne_110m_admin_0_countries.geojson')).json() }
    catch { el.innerHTML = '<p class="empty">The map could not be loaded.</p>'; return }
  }
  const W = el.clientWidth || 800, H = Math.round(W * 0.5)
  const projection = d3.geoNaturalEarth1().fitSize([W, H], { type: 'Sphere' })
  const path = d3.geoPath(projection)
  const max = d3.max([...byCountry.values()]) || 1
  const color = d3.scaleSequentialLog([1, Math.max(2, max)], d3.interpolate(css('--empty'), css('--bar')))
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${H}`)
  svg.append('path').attr('d', path({ type: 'Sphere' })).attr('fill', 'none').attr('stroke', css('--rule'))
  svg.selectAll(null).data(world.features).join('path').attr('d', path)
    .attr('fill', (f) => { const n = byCountry.get(f.properties.ISO_A2_EH); return n ? color(n) : css('--empty') })
    .attr('stroke', css('--surface')).attr('stroke-width', 0.5)
    .on('mousemove', (e, f) => showTip(e, `${f.properties.NAME}: ${byCountry.get(f.properties.ISO_A2_EH) || 0} page views`)).on('mouseleave', hideTip)
  el.replaceChildren(svg.node())
  document.getElementById('mapnote').textContent = byCountry.size ? `${byCountry.size} countries; darker is more page views.` : 'No visits counted yet.'
}
async function load() {
  const r = await fetch('/api/review/stats?days=' + days)
  if (r.status === 401) { location.href = './'; return }
  const { since, rows, visitors, humans = [], reports } = await r.json()
  const dayList = []
  for (let t = Date.parse(since + 'T00:00:00Z'); t <= Date.now(); t += 86400000) dayList.push(new Date(t).toISOString().slice(0, 10))
  const byDay = (kind) => { const m = new Map(); for (const x of rows) if (x.kind === kind) m.set(x.day, (m.get(x.day) || 0) + x.n); return m }
  const vis = new Map(visitors.map((v) => [v.day, v.n])), hum = new Map(humans.map((v) => [v.day, v.n]))
  const total = (kind) => rows.filter((x) => x.kind === kind).reduce((a, x) => a + x.n, 0)
  const visitorDays = visitors.reduce((a, v) => a + v.n, 0), peopleDays = humans.reduce((a, v) => a + v.n, 0)
  const hits = sum(rows, 'hit', (x) => x.item), botHits = hits.filter(([k]) => k.startsWith('bot')).reduce((a, h) => a + h[1], 0)
  const allHits = hits.reduce((a, h) => a + h[1], 0)
  const tiles = [
    [visitorDays, 'visitor-days'], [peopleDays, 'people (did something)'], [total('page'), 'pages viewed'], [total('play'), 'times the tapes were played'],
    [total('listen') / 60, 'hours of tape listened'], [total('highlight'), 'highlights played'], [total('photo'), 'photos opened'],
    [reports.reduce((a, v) => a + v.n, 0), 'reports sent'], [allHits ? Math.round(100 * botHits / allHits) : 0, '% of page requests from bots'],
  ]
  document.getElementById('tiles').innerHTML = tiles.map(([n, l]) => `<div class="tile"><b>${fmt(n)}</b><span>${l}</span></div>`).join('')
  lines('daily', dayList, [{ name: 'page views', color: '--c2', values: byDay('page') }, { name: 'visitors', color: '--bar', values: vis }, { name: 'people', color: '--c3', values: hum }])
  const byCountry = new Map(sum(rows, 'country', (x) => x.item))
  drawMap(byCountry)
  const src = sum(rows, 'landing', (x) => x.item)
  const cat = (k) => k === 'direct' ? 'Typed or bookmarked' : k.startsWith('search:') ? 'Search' : k.startsWith('social:') ? 'Social media' : 'Links on other sites'
  const cats = new Map(); for (const [k, n] of src) cats.set(cat(k), (cats.get(cat(k)) || 0) + n)
  split('kinds', [['Search', cats.get('Search') || 0, '--c2'], ['Social media', cats.get('Social media') || 0, '--c3'], ['Links on other sites', cats.get('Links on other sites') || 0, '--bar'], ['Typed or bookmarked', cats.get('Typed or bookmarked') || 0, '--muted']])
  table('sources', src.filter(([k]) => k !== 'direct'), (k) => k.replace(/^(search|social|link):/, (m0, t) => ({ search: 'Search · ', social: 'Social · ', link: '' })[t]))
  split('humans', [['browsers', allHits - botHits, '--c3'], ['bots', botHits, '--bar']])
  table('bots', [...hits.filter(([k]) => k.startsWith('bot')).map(([k, n]) => [k.slice(5), n]), ...sum(rows, 'bot', (x) => x.item + ' (ran the page)')], (k) => k)
  const off = -new Date().getTimezoneOffset() / 60, hrs = sum(rows, 'hour', (x) => x.item)
  const local = Array(24).fill(0); for (const [h, n] of hrs) local[((Number(h) + off) % 24 + 24) % 24] += n
  bars('hours', [...Array(24).keys()].map(String), local, '--c2', 150, (l, v) => `${l}:00 to ${l}:59 · ${v} visits`)
  const ld = byDay('listen'); bars('listenDaily', dayList.map((d) => d.slice(5)), dayList.map((d) => Math.round((ld.get(d) || 0) / 6) / 10), '--bar', 150, (l, v) => `${l}: ${v} h`)
  table('devices', sum(rows, 'device', (x) => x.item), (k) => k[0].toUpperCase() + k.slice(1))
  table('browsers', sum(rows, 'browser', (x) => x.item))
  table('missions', sum(rows, 'mission', (x) => x.mission), mname)
  table('listened', sum(rows, 'listen', (x) => x.mission), mname, (n) => (n / 60).toFixed(1) + ' h')
  table('highlights', sum(rows, 'highlight', (x) => x.item))
  table('mhours', sum(rows, 'listen', (x) => mname(x.mission) + ', hour ' + x.item), (k) => k, (n) => n + ' min')
  table('pages', sum(rows, 'page', (x) => x.item))
  table('countries', [...byCountry.entries()].sort((a, b) => b[1] - a[1]), country)
  table('reacts', sum(rows, 'react', (x) => x.item + ' ' + mname(x.mission)))
  photos(sum(rows, 'photo', (x) => x.item).slice(0, 48))
}
// A photo by its id: a film frame ("AS11-40-5875": our cleaned copy, else the film scan) or a NASA
// image ("S69-25862"): the picture to try first, the ones after it, and where it comes from.
const MEDIA = 'https://pub-7070d40e34dc47deaf91a77ffc426969.r2.dev'
function photoSources(id) {
  const m = /^AS(\d\d)-/i.exec(id)
  if (m) return {
    thumbs: [`${MEDIA}/photos/${m[1]}/${id}.thumb.jpg`, `https://tothemoon.im-ldi.com/data_a70/${id.slice(0, 4).toUpperCase()}/extra/${id}.thumb.png`, `https://tothemoon.im-ldi.com/data_a/${id.slice(0, 4).toUpperCase()}/png/${id}_THM.png`],
    fulls: [`${MEDIA}/photos/${m[1]}/${id}.jpg`, `https://tothemoon.im-ldi.com/data_a70/${id.slice(0, 4).toUpperCase()}/extra/${id}.small.png`, `https://tothemoon.im-ldi.com/data_a/${id.slice(0, 4).toUpperCase()}/png/${id}_SML.png`],
    source: `https://tothemoon.im-ldi.com/gallery/Apollo/${Number(m[1])}`, label: 'Apollo Image Gallery (ASU)' }
  const n = id.toLowerCase()
  return { thumbs: [`https://images-assets.nasa.gov/image/${id}/${id}~small.jpg`, `https://images-assets.nasa.gov/image/${n}/${n}~small.jpg`],
    fulls: [`https://images-assets.nasa.gov/image/${id}/${id}~large.jpg`, `https://images-assets.nasa.gov/image/${n}/${n}~large.jpg`],
    source: `https://images.nasa.gov/details/${id}`, label: 'NASA Image Library' }
}
function tryNext(img, list) {   // on a failed picture, the next address in its list
  img.onerror = () => { const next = list.shift(); if (next) img.src = next; else img.onerror = null }
  img.src = list.shift()
}
function photos(entries) {
  const el = document.getElementById('photos')
  if (!entries.length) { el.innerHTML = '<p class="empty">Nothing yet.</p>'; return }
  el.innerHTML = entries.map(([id, n]) => `<button data-id="${esc(id)}" title="${esc(id)}"><img alt="${esc(id)}" loading="lazy"><span><b>${esc(id)}</b> · ${n}×</span></button>`).join('')
  el.querySelectorAll('button').forEach((b) => tryNext(b.querySelector('img'), photoSources(b.dataset.id).thumbs))
}
const viewer = document.getElementById('viewer')
document.getElementById('photos').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return
  const src = photoSources(b.dataset.id)
  tryNext(viewer.querySelector('img'), src.fulls.slice())
  viewer.querySelector('p').innerHTML = `${esc(b.dataset.id)} · <a href="${src.source}" target="_blank" rel="noreferrer">${src.label} ↗</a> · tap anywhere to close`
  viewer.style.display = 'flex'
})
viewer.addEventListener('click', (e) => { if (!e.target.closest('a')) viewer.style.display = 'none' })
addEventListener('keydown', (e) => { if (e.key === 'Escape') viewer.style.display = 'none' })
document.querySelector('.bar').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return
  days = Number(b.dataset.d)
  document.querySelectorAll('.bar button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
  load()
})
let resizeTimer = null
addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(load, 300) })
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
