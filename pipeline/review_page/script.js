const FRAMES = __FRAMES__;
// Reviewer dials. Formulas and step sizes match pipeline/process_photos.py
// (tone_curve, adjust_colour, straighten): keep the two in step.
const DIALS = [
  {k: 'brightness', label: 'Brightness', group: 'Tone'},
  {k: 'contrast', label: 'Contrast', group: 'Tone'},
  {k: 'shadows', label: 'Shadows', group: 'Tone'},
  {k: 'highlights', label: 'Highlights', group: 'Tone'},
  {k: 'warmth', label: 'Warmth', group: 'Colour'},
  {k: 'tint', label: 'Tint', group: 'Colour'},
  {k: 'saturation', label: 'Saturation', group: 'Colour'},
  {k: 'straighten', label: 'Straighten', group: 'Angle', min: -10, max: 10, step: 0.5, unit: '°'},
];
const KEYS = [...DIALS.map(d => d.k), 'rotate'];
const TOGGLES = [['colour', 'Colour off'], ['crop', 'Bad crop']];
const MID_GAMMA = 0.85, SHOULDER = 0.12;
const BSTEP = Math.sqrt(0.8), CSTEP = 0.55, TSTEP = 10, SATSTEP = 0.1, COLSTEP = 1.5;
const DEFAULT_BRIGHTNESS = -2, DEFAULT_CONTRAST = -1;   // the reviewed default look (process_photos.py)

const $ = id => document.getElementById(id);
const reviews = {};          // frame id -> saved review
const drafts = {};           // frame id -> dial values being dragged, not yet saved
const undoSteps = [];          // undo steps: {id, prev} (prev = the review before the change, or null)
const byId = Object.fromEntries(FRAMES.map(f => [f.id, f]));
let db = null, userNs = null, myId = null, canWrite = false;
let queue = FRAMES.map(f => f.id), cur = null, compareWith = null;

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const num = (r, k) => (r && r[k]) || 0;
const rendered = (f, k) => (f.rendered && f.rendered[k]) || 0;
const values = id => ({...Object.fromEntries(KEYS.map(k => [k, num(reviews[id], k)])), ...(drafts[id] || {})});
const pendingKeys = (v, f) => KEYS.filter(k => v[k] !== rendered(f, k));
function stateOf(id) {
  const r = reviews[id], f = byId[id];
  if (!r) return ['todo', 'To review'];
  if (r.verdict === 'good') return ['good', 'Looks good'];
  if (r.verdict === 'reject') return ['reject', 'Rejected'];
  if (pendingKeys(values(id), f).length || r.colour || r.crop || r.verdict === 'note') return ['flag', 'Needs work'];
  return ['todo', 'Check again'];
}
const signed = v => v === 0 ? '0' : (v > 0 ? '+' : '−') + Math.abs(v);
const fmt = (d, v) => signed(v) + (d.unit || '');
const rotLabel = v => ({0: 'none', 90: '90° right', 180: '180°', 270: '90° left'}[v]);
function ago(iso) {
  const s = (Date.now() - Date.parse(iso)) / 1000;
  if (!isFinite(s)) return '';
  if (s < 60) return 'just now';
  if (s < 3600) return Math.round(s / 60) + ' min ago';
  if (s < 86400) return Math.round(s / 3600) + ' h ago';
  return new Date(iso).toLocaleDateString();
}
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* not kept this visit */ } },
};

// ---------- building the controls once ----------
let group = '';
$('panel').innerHTML = DIALS.map(d => {
  const head = d.group !== group ? `<div class="group-label">${(group = d.group)}</div>` : '';
  return `${head}<div class="dial" data-k="${d.k}"><label for="dial-${d.k}">${d.label}</label><input type="range" id="dial-${d.k}" min="${d.min ?? -8}" max="${d.max ?? 8}" step="${d.step ?? 1}" value="0"><output for="dial-${d.k}">0</output></div>`;
}).join('');
$('flags').innerHTML = TOGGLES.map(([k, label]) => `<button type="button" data-k="${k}" aria-pressed="false">${label}</button>`).join('');
const dialRows = [...document.querySelectorAll('.dial')];
const toggles = [...document.querySelectorAll('#flags button')];
const writable = () => [$('good'), $('reject'), $('note'), $('reset'), ...toggles, ...dialRows.map(r => r.querySelector('input')), ...document.querySelectorAll('[data-rot]')];

$('strip').innerHTML = FRAMES.map(f => `<button type="button" data-id="${f.id}" aria-label="${f.id}" aria-current="false"><img src="${f.thumb}" alt="" loading="lazy"></button>`).join('');
const thumbs = Object.fromEntries([...document.querySelectorAll('#strip button')].map(b => [b.dataset.id, b]));

// ---------- showing a photo ----------
function show(id) {
  if (!byId[id]) return;
  if (cur && cur !== id) { commitDraft(cur); for (const k in baseCache) if (!k.startsWith(id + ':')) delete baseCache[k]; }
  cur = id; compareWith = null;
  store.set('apollo-review-at', id);
  const f = byId[id];
  $('title').innerHTML = `Apollo ${f.mission} <span class="fid">${f.id}</span>`;
  $('cap').textContent = f.caption || '';
  $('cap').hidden = !f.caption;
  const refs = [['raw', 'Raw scan', f.raw]];
  if (f.before) refs.push(['before', 'First version', f.before]);
  if (f.nasa) refs.push(['nasa', "NASA's release", f.nasa]);
  $('compare').innerHTML = '<span>Compare:</span>' + refs.map(([k, label, src]) => `<button type="button" data-cmp="${k}" aria-pressed="false"><img src="${src}" alt="">${label}</button>`).join('');
  $('photo').src = f.ours;
  $('photo').alt = `Apollo ${f.mission} frame ${f.id}, our cleanup`;
  $('preview').hidden = true; $('photo').hidden = false; $('alt').hidden = true;
  drawn = null;
  resetZoom();
  Object.values(thumbs).forEach(b => b.setAttribute('aria-current', String(b.dataset.id === id)));
  thumbs[id].scrollIntoView({block: 'nearest', inline: 'nearest'});
  paint();
  schedulePreview(true);
}
function move(step) {
  const i = queue.indexOf(cur);
  const j = i < 0 ? 0 : i + step;
  if (j >= 0 && j < queue.length) show(queue[j]);
}

function paint() {
  if (!cur) return;
  const id = cur, f = byId[id], r = reviews[id], v = values(id), [st, label] = stateOf(id);
  $('status').textContent = label; $('status').dataset.state = st;
  $('good').setAttribute('aria-pressed', String(st === 'good'));
  $('reject').setAttribute('aria-pressed', String(st === 'reject'));
  dialRows.forEach(row => {
    const d = DIALS.find(x => x.k === row.dataset.k), input = row.querySelector('input');
    if (!(drafts[id] && document.activeElement === input)) input.value = v[d.k];
    row.querySelector('output').textContent = fmt(d, v[d.k]);
    row.dataset.set = String(v[d.k] !== rendered(f, d.k));
  });
  $('rot').textContent = rotLabel(v.rotate);
  toggles.forEach(b => b.setAttribute('aria-pressed', String(!!(r && r[b.dataset.k]))));
  if (document.activeElement !== $('note')) $('note').value = (r && r.note) || '';
  writable().forEach(x => { x.disabled = !canWrite; });
  const i = queue.indexOf(id);
  $('pos').textContent = i < 0 ? '–' : `${i + 1} / ${queue.length}`;
  $('prev').disabled = i <= 0; $('next').disabled = i < 0 || i >= queue.length - 1;
  paintHint();
}
async function paintHint() {
  const id = cur, r = reviews[id], pend = pendingKeys(values(id), byId[id]).length > 0;
  let who = '';
  if (r && r.by) who = `${r.verdict === 'check' ? 'Re-run after marks' : 'Marked'} by ${await nameOf(r.by)}, ${ago(r.at)}.`;
  if (id !== cur) return;
  $('hint').innerHTML = (pend ? '<b>Preview.</b> Saved; the full-size photo gets these settings on the next run. ' : '') + esc(who);
}
function paintThumb(id) { thumbs[id].dataset.state = stateOf(id)[0]; }
function paintCounts() {
  const n = {todo: 0, good: 0, flag: 0, reject: 0};
  FRAMES.forEach(f => n[stateOf(f.id)[0]]++);
  $('counts').innerHTML = `<span><b>${n.good}</b>/${FRAMES.length} good</span><span class="extra"><b>${n.flag}</b> need work</span><span class="extra"><b>${n.todo}</b> to review</span><span class="extra"><b>${n.reject}</b> rejected</span>`;
}
const profileCache = {};
async function nameOf(by) {
  if (by === myId) return 'you';
  if (!userNs) return 'Someone';
  if (!(by in profileCache)) profileCache[by] = (await userNs.profiles([by]))[by].name || 'Someone';
  return profileCache[by];
}
// A filter picks its photos when you choose it; photos don't drop out while you work on them.
function applyFilter(value) {
  queue = FRAMES.map(f => f.id).filter(id => value === 'all' || stateOf(id)[0] === value);
  FRAMES.forEach(f => { thumbs[f.id].hidden = !queue.includes(f.id); });
  if (queue.length && !queue.includes(cur)) show(queue[0]); else paint();
}

// ---------- saving, with undo ----------
const chains = {};
function save(id, body, record = true) {
  const prev = reviews[id] ? {...reviews[id]} : null;
  if (record) { undoSteps.push({id, prev}); $('undo').disabled = false; }
  if (body) reviews[id] = body; else delete reviews[id];
  delete drafts[id];
  afterChange(id);
  if (!db) return;
  const ref = db.collection('reviews').doc(id);
  chains[id] = (chains[id] || Promise.resolve()).then(() => body ? ref.set(body) : ref.delete()).catch(e => {
    if (prev) reviews[id] = prev; else delete reviews[id];
    if (e && e.code === 'invalid_argument') canWrite = false;
    afterChange(id);
  });
}
function afterChange(id) {
  paintThumb(id); paintCounts();
  if (id === cur) { paint(); schedulePreview(true); }
}
function undo() {
  const step = undoSteps.pop();
  $('undo').disabled = undoSteps.length === 0;
  if (!step) return;
  if (step.id !== cur) show(step.id);
  save(step.id, step.prev, false);
}
const blank = () => ({...Object.fromEntries(KEYS.map(k => [k, 0])), colour: false, crop: false, note: ''});
const current = id => ({...blank(), ...(reviews[id] || {}), ...(drafts[id] || {})});
const stamp = r => Object.assign(r, {by: myId, at: new Date().toISOString()});
function commit(id, r) {
  const f = byId[id], pend = pendingKeys(r, f).length > 0;
  if (!pend && !r.colour && !r.crop && !r.note && !f.rendered) return save(id, null);
  if ((r.verdict === 'good' && !r.colour && !r.crop) || r.verdict === 'reject') return save(id, stamp(r));   // adjusting an approved photo keeps it approved
  r.verdict = (pend || r.colour || r.crop) ? 'flag' : (r.note && !f.rendered ? 'note' : 'check');
  save(id, stamp(r));
}
function commitDraft(id) {
  if (!drafts[id]) return;
  const r = current(id), was = {...blank(), ...(reviews[id] || {})};
  if (KEYS.every(k => r[k] === was[k])) { delete drafts[id]; return; }
  commit(id, r);
}
// Reject: a bad or unusable frame (fogged, blank, badly blurred). It's left
// off the site and skipped by the pipeline; un-reject by tapping again.
function toggleReject() {
  const id = cur, r = current(id);
  if (r.verdict === 'reject') { delete r.verdict; return commit(id, r); }
  r.verdict = 'reject';
  save(id, stamp(r));
  setTimeout(() => { if (cur === id) move(1); }, 250);
}
function toggleGood() {
  const id = cur, r = current(id);
  if (r.verdict === 'good') { delete r.verdict; return commit(id, r); }
  r.colour = false; r.crop = false; r.verdict = 'good';
  save(id, stamp(r));
  setTimeout(() => { if (cur === id) move(1); }, 250);   // on to the next photo
}

// ---------- zoom ----------
const stage = $('stage'), zoomer = $('zoomer');
let Z = {s: 1, x: 0, y: 0};
function clampZoom() {
  const sw = stage.clientWidth, sh = stage.clientHeight;
  Z.s = Math.min(8, Math.max(1, Z.s));
  Z.x = Math.min(0, Math.max(sw * (1 - Z.s), Z.x));
  Z.y = Math.min(0, Math.max(sh * (1 - Z.s), Z.y));
}
function applyZoom() {
  clampZoom();
  zoomer.style.transform = `translate(${Z.x}px, ${Z.y}px) scale(${Z.s})`;
  stage.classList.toggle('zoomed', Z.s > 1.01);
}
function zoomAt(px, py, s) {
  const k = s / Z.s;
  Z.x = px - (px - Z.x) * k; Z.y = py - (py - Z.y) * k; Z.s = s;
  applyZoom();
}
function resetZoom() { Z = {s: 1, x: 0, y: 0}; applyZoom(); }
function toggleZoom(px, py) { if (Z.s > 1.01) resetZoom(); else zoomAt(px, py, 2.5); }
const pointers = new Map();
let gesture = null;
stage.addEventListener('pointerdown', e => {
  if (e.target.closest('.zoom-ctl')) return;
  stage.setPointerCapture(e.pointerId);
  const rect = stage.getBoundingClientRect();
  pointers.set(e.pointerId, {x: e.clientX - rect.left, y: e.clientY - rect.top});
  const pts = [...pointers.values()];
  if (pts.length === 1) gesture = {kind: 'pan', x0: e.clientX, y0: e.clientY, zx: Z.x, zy: Z.y, t: Date.now(), moved: false};
  else if (pts.length === 2) {
    const [a, b] = pts;
    gesture = {kind: 'pinch', d0: Math.hypot(a.x - b.x, a.y - b.y) || 1, s0: Z.s, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, zx: Z.x, zy: Z.y};
  }
});
stage.addEventListener('pointermove', e => {
  if (!pointers.has(e.pointerId)) return;
  const rect = stage.getBoundingClientRect();
  pointers.set(e.pointerId, {x: e.clientX - rect.left, y: e.clientY - rect.top});
  if (!gesture) return;
  if (gesture.kind === 'pan') {
    const dx = e.clientX - gesture.x0, dy = e.clientY - gesture.y0;
    if (Math.hypot(dx, dy) > 6) gesture.moved = true;
    if (Z.s > 1.01) { Z.x = gesture.zx + dx; Z.y = gesture.zy + dy; applyZoom(); }
  } else if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    const s = gesture.s0 * Math.hypot(a.x - b.x, a.y - b.y) / gesture.d0;
    const k = Math.min(8, Math.max(1, s)) / gesture.s0;
    Z.s = gesture.s0 * k;
    Z.x = gesture.mx - (gesture.mx - gesture.zx) * k + ((a.x + b.x) / 2 - gesture.mx);
    Z.y = gesture.my - (gesture.my - gesture.zy) * k + ((a.y + b.y) / 2 - gesture.my);
    applyZoom();
  }
});
function endPointer(e) {
  if (!pointers.has(e.pointerId)) return;
  const rect = stage.getBoundingClientRect();
  if (gesture && gesture.kind === 'pan' && pointers.size === 1 && !gesture.moved && Date.now() - gesture.t < 400) {
    toggleZoom(e.clientX - rect.left, e.clientY - rect.top);
  }
  pointers.delete(e.pointerId);
  gesture = pointers.size === 1 ? (() => { const [p] = pointers.values(); return {kind: 'pan', x0: p.x + rect.left, y0: p.y + rect.top, zx: Z.x, zy: Z.y, t: 0, moved: true}; })() : null;
}
stage.addEventListener('pointerup', endPointer);
stage.addEventListener('pointercancel', endPointer);
stage.addEventListener('wheel', e => {
  e.preventDefault();
  const rect = stage.getBoundingClientRect();
  zoomAt(e.clientX - rect.left, e.clientY - rect.top, Math.min(8, Math.max(1, Z.s * Math.exp(-e.deltaY * 0.0015))));
}, {passive: false});
$('zoom-in').addEventListener('click', () => zoomAt(stage.clientWidth / 2, stage.clientHeight / 2, Math.min(8, Z.s * 1.6)));
$('zoom-out').addEventListener('click', () => { const s = Z.s / 1.6; if (s <= 1.05) resetZoom(); else zoomAt(stage.clientWidth / 2, stage.clientHeight / 2, s); });
window.addEventListener('resize', applyZoom);

// ---------- live preview ----------
function tone(L, v) {
  const b = v.brightness + DEFAULT_BRIGHTNESS, c = v.contrast + DEFAULT_CONTRAST;
  let x = Math.pow(Math.min(Math.max(L, 0), 100) / 100, MID_GAMMA * Math.pow(BSTEP, b)) * 100;
  if (c) {
    const k = CSTEP * Math.abs(c);
    let d = (x - 50) / 50;
    d = c > 0 ? Math.tanh(k * d) / Math.tanh(k) : Math.atanh(Math.max(-1, Math.min(1, d)) * Math.tanh(k)) / k;
    x = 50 + 50 * d;
  }
  x = x - SHOULDER * 100 * Math.pow(x / 100, 3);
  if (v.shadows || v.highlights) {
    const t = x / 100;
    x = x + TSTEP * (v.shadows * t * (1 - t) * (1 - t) + v.highlights * (1 - t) * t * t);
  }
  return x;
}
const TO_LIN = new Float32Array(256).map((_, i) => { const v = i / 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
const TO_SRGB = new Uint8ClampedArray(4097).map((_, i) => { const v = i / 4096; return 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055) + 0.5; });
const M = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], W = [0.95047, 1, 1.08883];
const MI = (() => {
  const [[a, b, c], [d, e, f], [g, h, i]] = M, det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
  return [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
          [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
          [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]];
})();
const fLab = t => t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116;
const fInv = t => t > 0.2069 ? t * t * t : (t - 16 / 116) / 7.787;

// The photo as shown was made with the frame's `rendered` settings. Undo
// those once (back to pre-dial lightness and colour) and cache the result,
// small for dragging and full size for when you let go.
const baseCache = {};
async function base(id, full) {
  const key = id + ':' + (full ? 'full' : 'small');
  if (baseCache[key]) return baseCache[key];
  const f = byId[id], R = Object.fromEntries(KEYS.map(k => [k, rendered(f, k)]));
  const img = new Image();
  img.src = f.ours;
  await img.decode();
  const scale = full ? 1 : Math.min(1, 800 / Math.max(img.naturalWidth, img.naturalHeight));
  const w = Math.round(img.naturalWidth * scale), h = Math.round(img.naturalHeight * scale);
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0, w, h);
  const px = ctx.getImageData(0, 0, w, h).data;
  const N = 2000, fwd = new Float64Array(N + 1);
  for (let i = 0; i <= N; i++) fwd[i] = tone(100 * i / N, R);
  const inv = new Float32Array(1001);
  for (let i = 0, j = 0; i <= 1000; i++) {
    const Ls = i / 10;
    while (j < N && fwd[j + 1] < Ls) j++;
    const span = j < N ? fwd[j + 1] - fwd[j] : 0;
    // Pixels a touch brighter than the curve's top (JPEG ringing on clouds) map to white, never past it.
    inv[i] = Math.min(100, 100 * (j + (span > 0 ? Math.max(0, Math.min(1, (Ls - fwd[j]) / span)) : 0)) / N);
  }
  const satR = 1 + SATSTEP * R.saturation;
  const L0 = new Float32Array(w * h), A0 = new Float32Array(w * h), B0 = new Float32Array(w * h), fade = new Float32Array(w * h);
  for (let p = 0, q = 0; p < px.length; p += 4, q++) {
    const r = TO_LIN[px[p]], g = TO_LIN[px[p + 1]], b = TO_LIN[px[p + 2]];
    const fx = fLab((M[0][0] * r + M[0][1] * g + M[0][2] * b) / W[0]);
    const fy = fLab((M[1][0] * r + M[1][1] * g + M[1][2] * b) / W[1]);
    const fz = fLab((M[2][0] * r + M[2][1] * g + M[2][2] * b) / W[2]);
    const L = inv[Math.max(0, Math.min(1000, Math.round((116 * fy - 16) * 10)))];
    const fd = Math.min(Math.max(L / 10, 0), 1) * Math.min(Math.max((100 - L) / 5, 0), 1);
    L0[q] = L; fade[q] = fd;
    A0[q] = (500 * (fx - fy) - COLSTEP * R.tint * fd) / satR;
    B0[q] = (200 * (fy - fz) - COLSTEP * R.warmth * fd) / satR;
  }
  const off = document.createElement('canvas'); off.width = w; off.height = h;
  return (baseCache[key] = {w, h, L0, A0, B0, fade, off, data: off.getContext('2d').createImageData(w, h)});
}

let frame = 0, wantFull = false, drawn = null;
function schedulePreview(full) {
  wantFull = wantFull || !!full;
  if (!frame) frame = requestAnimationFrame(() => { frame = 0; const fl = wantFull; wantFull = false; drawPreview(cur, fl); });
}
async function drawPreview(id, full) {
  if (!id) return;
  const f = byId[id], v = values(id), canvas = $('preview');
  const turn = ((v.rotate - rendered(f, 'rotate')) % 360 + 360) % 360;
  const same = turn === 0 && DIALS.every(d => v[d.k] === rendered(f, d.k));
  if (same) { canvas.hidden = true; $('photo').hidden = !!compareWith; drawn = null; return; }
  const key = [...DIALS.map(d => v[d.k]), turn, full ? 'F' : 's'].join(',');
  if (drawn === key) return;
  let B;
  try { B = await base(id, full); } catch (e) { return; }
  const now = values(id);
  if (cur !== id || KEYS.some(k => now[k] !== v[k])) return;   // moved on while loading; a newer draw is queued
  const lut = new Float32Array(1001);
  for (let i = 0; i <= 1000; i++) lut[i] = tone(i / 10, v);
  const sat = 1 + SATSTEP * v.saturation, tA = COLSTEP * v.tint, tB = COLSTEP * v.warmth;
  const {w, h, L0, A0, B0, fade, off, data} = B, px = data.data;
  for (let q = 0, p = 0; q < L0.length; q++, p += 4) {
    const L = lut[Math.max(0, Math.min(1000, Math.round(L0[q] * 10)))];
    const fy = (L + 16) / 116, fx = fy + (A0[q] * sat + tA * fade[q]) / 500, fz = fy - (B0[q] * sat + tB * fade[q]) / 200;
    const X = fInv(fx) * W[0], Y = fInv(fy) * W[1], Z3 = fInv(fz) * W[2];
    for (let ch = 0; ch < 3; ch++) {
      const lin = MI[ch][0] * X + MI[ch][1] * Y + MI[ch][2] * Z3;
      px[p + ch] = TO_SRGB[Math.max(0, Math.min(4096, Math.round(lin * 4096)))];
    }
    px[p + 3] = 255;
  }
  off.getContext('2d').putImageData(data, 0, 0);
  // Quarter turns swap the canvas's sides; straighten turns a little more and
  // zooms just enough to hide the corners, as the pipeline crops.
  const quarter = turn === 90 || turn === 270, cw = quarter ? h : w, ch = quarter ? w : h;
  if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch; }
  const th = (v.straighten - rendered(f, 'straighten')) * Math.PI / 180;
  const k = Math.cos(Math.abs(th)) + Math.max(w / h, h / w) * Math.sin(Math.abs(th));
  const ctx = canvas.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, cw, ch);
  ctx.translate(cw / 2, ch / 2); ctx.rotate(turn * Math.PI / 180 + th); ctx.scale(k, k);
  ctx.drawImage(off, -w / 2, -h / 2);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  drawn = key;
  if (!compareWith) { canvas.hidden = false; $('photo').hidden = true; }
}

// ---------- compare ----------
$('compare').addEventListener('click', e => {
  const b = e.target.closest('[data-cmp]'); if (!b) return;
  const f = byId[cur], which = b.dataset.cmp;
  compareWith = compareWith === which ? null : which;
  document.querySelectorAll('[data-cmp]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.cmp === compareWith)));
  const alt = $('alt'), label = $('stage-label');
  if (compareWith) {
    alt.src = f[compareWith]; alt.hidden = false; $('photo').hidden = true; $('preview').hidden = true;
    label.textContent = `${b.textContent.trim()}, tap its button again to go back`; label.hidden = false;
  } else {
    alt.hidden = true; label.hidden = true; $('photo').hidden = false; drawn = null; schedulePreview(true);
  }
});

// ---------- controls ----------
dialRows.forEach(row => {
  const input = row.querySelector('input'), k = row.dataset.k;
  // While dragging: a quick preview. On release: save once, then a full-size preview.
  input.addEventListener('input', () => { drafts[cur] = {...(drafts[cur] || {}), [k]: +input.value}; paint(); schedulePreview(false); });
  input.addEventListener('change', () => { commitDraft(cur); schedulePreview(true); });
});
document.querySelectorAll('[data-rot]').forEach(b => b.addEventListener('click', () => {
  const r = current(cur);
  r.rotate = ((r.rotate + +b.dataset.rot) % 360 + 360) % 360;
  commit(cur, r);
}));
$('reset').addEventListener('click', () => { const r = current(cur); KEYS.forEach(k => { r[k] = rendered(byId[cur], k); }); commit(cur, r); });
toggles.forEach(b => b.addEventListener('click', () => { const r = current(cur); r[b.dataset.k] = !r[b.dataset.k]; commit(cur, r); }));
$('note').addEventListener('change', () => {
  const note = $('note').value.trim(), r = current(cur);
  if ((r.note || '') === note) return;
  r.note = note; commit(cur, r);
});
$('good').addEventListener('click', toggleGood);
$('reject').addEventListener('click', toggleReject);
$('undo').addEventListener('click', undo);
$('prev').addEventListener('click', () => move(-1));
$('next').addEventListener('click', () => move(1));
$('filter').addEventListener('change', e => applyFilter(e.target.value));
$('strip').addEventListener('click', e => { const b = e.target.closest('button[data-id]'); if (b) show(b.dataset.id); });
document.addEventListener('keydown', e => {
  const t = e.target, typing = t.tagName === 'INPUT' && t.type === 'text';
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !typing) { e.preventDefault(); undo(); return; }
  if (typing || e.ctrlKey || e.metaKey || e.altKey) return;
  const onSlider = t.tagName === 'INPUT' && t.type === 'range';
  if (!onSlider && e.key === 'ArrowLeft') { e.preventDefault(); move(-1); }
  else if (!onSlider && e.key === 'ArrowRight') { e.preventDefault(); move(1); }
  else if (e.key === 'z' || e.key === 'Z') toggleZoom(stage.clientWidth / 2, stage.clientHeight / 2);
});

// ---------- start ----------
FRAMES.forEach(f => paintThumb(f.id));
paintCounts();
show(byId[store.get('apollo-review-at')] ? store.get('apollo-review-at') : FRAMES[0].id);

(async () => {
  const use = window.claude && window.claude.use ? n => window.claude.use(n) : async () => null;
  const [dbNs, u] = await Promise.all([use('db'), use('user')]);
  userNs = u;
  if (!dbNs) { $('offline').hidden = false; return; }
  db = dbNs;
  myId = u ? await u.id() : null;
  const allowed = u ? await u.can('data.write') : null;
  canWrite = allowed !== false;
  if (!canWrite) {
    $('offline').textContent = 'You can see the reviews but not change them. Ask the page owner for “Can interact” access to review.';
    $('offline').hidden = false;
  }
  let first = true;
  db.collection('reviews').onSnapshot(snap => {
    const changed = new Set();
    snap.docChanges().forEach(ch => {
      const id = ch.doc.id;
      if (!byId[id]) return;
      if (ch.type === 'removed') delete reviews[id]; else reviews[id] = ch.doc.data();
      changed.add(id);
    });
    changed.forEach(id => paintThumb(id));
    if (changed.size) paintCounts();
    if (changed.has(cur) || first) { paint(); schedulePreview(true); }
    const at = store.get('apollo-review-at');
    if (first && (!byId[at] || stateOf(at)[0] === 'good')) {   // start at the first photo still to review
      const next = FRAMES.find(f => stateOf(f.id)[0] !== 'good');
      if (next) show(next.id);
    }
    first = false;
  }, () => { $('offline').hidden = false; });
})();
