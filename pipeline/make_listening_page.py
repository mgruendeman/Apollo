"""Build a listening page to compare original and cleaned-up samples.

Point it at the folder process_audio.py wrote samples into (files named
<sample>.original.m4a, <sample>.clean12.m4a, ...). It writes listen.html:
one row per sample, buttons that switch between versions at the same moment
in the recording, the measured background noise of each version, and a
choice of the best one per sample that can be copied back as text.

    python pipeline/make_listening_page.py samples/            # samples/listen.html, files linked
    python pipeline/make_listening_page.py samples/ --embed    # audio inside the page (to share it)

Needs: ffmpeg, numpy
"""
import argparse
import base64
import html
import json
import re
import subprocess
from pathlib import Path

import numpy as np

MISSION_TAPES = {'000-AAA': '8', '001-AAA': '8', '037-AAA': '8', '075-AAA': '9', '10-0': '10', '11-0': '11',
                 '375-AAA': '12', '219-AAP': '13', '405-AAA': '13', '415-AAA': '13', '461-AAA': '14',
                 '557-AAA': '15', '674-AAA': '16', '790-AAA': '17'}
ENGINES = {'ff': ('Basic', "ffmpeg's noise filter"), 'df': ('AI', 'DeepFilterNet'), 'clean': ('', 'noise reduction')}


def background_db(path):
    """Quiet-moment level (10th percentile of 20 ms frames), in dBFS."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    frames = a[: len(a) // 320 * 320].reshape(-1, 320)
    rms = 20 * np.log10(np.sqrt((frames ** 2).mean(1)) + 1e-9)
    return round(float(np.percentile(rms, 10)), 1)


def label(version):
    if version == 'original':
        return 'Original', 'NASA tape, loudness evened out only'
    if version == 'journal':
        return 'Journal clip', "apollojournals.org's version, loudness evened out only"
    m = re.match(r'([a-z]+?)(\d+)?$', version)
    engine, db = (m.group(1), m.group(2)) if m else ('clean', None)
    short, what = ENGINES.get(engine, ('', 'noise reduction'))
    if db is None:
        return (short or 'Cleaned'), what
    strength = 'gentle' if int(db) <= 12 else 'stronger'
    return (f'{short} {strength}' if short else strength.capitalize()), f'{what}, up to {db} dB'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--embed', action='store_true', help='put the audio inside the page')
    ap.add_argument('--out', help='where to write the page (default: <folder>/listen.html)')
    ap.add_argument('--engine', default='ffmpeg', help='which denoiser made the samples, shown on the page')
    args = ap.parse_args()
    folder = Path(args.folder).expanduser()

    samples = {}
    for f in sorted(folder.glob('*.m4a')):
        stem, version = f.name[:-4].rsplit('.', 1)
        samples.setdefault(stem, {})[version] = f
    # original first, then cleaned versions by strength, the journal's last
    order = lambda v: (v == 'journal', v != 'original', v.startswith('df'), int(re.sub(r'\D', '', v) or 0))

    data = []
    for stem, versions in samples.items():
        tape, _, start = stem.rpartition('_')
        mission = next((m for k, m in MISSION_TAPES.items() if tape.startswith(k)), '?')
        secs = int(start.rstrip('s')) if start.endswith('s') else 0
        at = f'{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}' if secs >= 3600 else f'{secs // 60}:{secs % 60:02d}'
        row = {'id': stem, 'mission': mission, 'tape': tape, 'at': at, 'versions': [],
               'note': '' if 'journal' in versions else 'No journal clip covers this moment.'}
        for v in sorted(versions, key=order):
            name, detail = label(v)
            src = (f'data:audio/mp4;base64,{base64.b64encode(versions[v].read_bytes()).decode()}'
                   if args.embed else versions[v].name)
            row['versions'].append({'key': v, 'name': name, 'detail': detail, 'src': src,
                                    'noise': background_db(versions[v])})
        data.append(row)

    page = TEMPLATE.replace('__DATA__', json.dumps(data)).replace('__ENGINE__', html.escape(args.engine))
    out = Path(args.out).expanduser() if args.out else folder / 'listen.html'
    out.write_text(page)
    print(f'wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(data)} samples)')


TEMPLATE = r'''<title>Apollo Tape Ear Check</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
:root {
  --ground: #eef1ee; --surface: #ffffff; --ink: #1b2320; --muted: #5d6a65; --rule: #d3dad6;
  --accent: #b8741a; --accent-ink: #ffffff; --chosen: #e9f3ea; --chosen-edge: #3f8a52;
  --mono: 'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace;
  --sans: 'Barlow', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #101513; --surface: #182019; --ink: #e3eae5; --muted: #98a69f; --rule: #2c3830;
    --accent: #e3a444; --accent-ink: #14100a; --chosen: #1d2e22; --chosen-edge: #6cc182; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --ground: #101513; --surface: #182019; --ink: #e3eae5; --muted: #98a69f; --rule: #2c3830;
  --accent: #e3a444; --accent-ink: #14100a; --chosen: #1d2e22; --chosen-edge: #6cc182; color-scheme: dark;
}
body { background: var(--ground); color: var(--ink); font: 16px/1.5 var(--sans); padding: 20px 16px 48px; }
main { max-width: 720px; margin: 0 auto; display: grid; gap: 18px; }
h1 { font-size: 1.7rem; line-height: 1.2; margin: 0; text-wrap: balance; }
.lede { margin: 6px 0 0; color: var(--muted); max-width: 62ch; }
.how { margin: 0; padding: 12px 14px; border-left: 3px solid var(--accent); background: var(--surface); font-size: .92rem; }
.how b { font-weight: 600; }
.sample { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px; display: grid; gap: 12px; }
.sample header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; }
.sample h2 { margin: 0; font-size: 1.05rem; }
.tape { font: 600 .78rem/1 var(--mono); color: var(--muted); letter-spacing: .02em; }
.versions { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr)); gap: 8px; }
.versions.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
@media (max-width: 560px) { .versions.four { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.v.journal { border-style: dashed; }
.note { margin: 0; font-size: .82rem; color: var(--muted); }
.v { display: grid; gap: 2px; align-content: start; text-align: left; padding: 10px; min-width: 0; overflow-wrap: anywhere; border: 1px solid var(--rule); border-radius: 8px;
     background: var(--ground); color: var(--ink); font: inherit; cursor: pointer; }
.v .name { font-weight: 700; display: flex; align-items: center; gap: 8px; }
.v .detail, .v .noise { font-size: .76rem; line-height: 1.35; color: var(--muted); }
.v .noise { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.v.playing { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
.v.playing .name::after { content: '▶'; font-size: .7rem; color: var(--accent); }
.v:focus-visible, .pick input:focus-visible + span, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.transport { display: flex; align-items: center; gap: 10px; }
.play { flex: none; width: 44px; height: 44px; border-radius: 50%; border: none; background: var(--accent); color: var(--accent-ink); font-size: 1rem; cursor: pointer; }
.transport input[type=range] { flex: 1; min-width: 0; accent-color: var(--accent); }
.time { font: .78rem var(--mono); color: var(--muted); font-variant-numeric: tabular-nums; min-width: 9ch; text-align: right; }
.picks { display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; font-size: .9rem; }
.picks > span { color: var(--muted); }
.pick { display: inline-flex; gap: 6px; align-items: center; cursor: pointer; }
.sample.decided { border-color: var(--chosen-edge); background: var(--chosen); }
.notes { width: 100%; box-sizing: border-box; font: inherit; font-size: .9rem; padding: 8px 10px; border: 1px solid var(--rule); border-radius: 8px; background: var(--ground); color: var(--ink); }
.summary { display: grid; gap: 10px; background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px; }
.summary h2 { margin: 0; font-size: 1.05rem; }
.copy { justify-self: start; padding: 10px 16px; border: none; border-radius: 8px; background: var(--accent); color: var(--accent-ink); font: 600 .95rem var(--sans); cursor: pointer; }
#result { width: 100%; box-sizing: border-box; min-height: 7em; font: .8rem/1.45 var(--mono); padding: 8px 10px; border: 1px solid var(--rule); border-radius: 8px; background: var(--ground); color: var(--ink); }
.status { font-size: .85rem; color: var(--chosen-edge); min-height: 1.3em; margin: 0; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
<main>
  <div>
    <h1>Apollo Tape Ear Check</h1>
    <p class="lede">Short samples from NASA's own mission tapes: the original, cleaned up with a basic noise filter and with an AI one (DeepFilterNet), each gentle and stronger, and where the Apollo Flight Journal has the same moment, its clip as a baseline. Cleaned versions also have steady whines and hums notched out. Pick the one that sounds best for listening to the missions.</p>
  </div>
  <p class="how"><b>How to compare:</b> press play, then tap between versions while it plays — it switches at the same moment in the recording, so you hear only the difference. Headphones help. "Background" is the level in the quiet moments between words: lower means less hiss. Cleaned with __ENGINE__.</p>
  <div id="samples"></div>
  <section class="summary" aria-labelledby="sum-h">
    <h2 id="sum-h">Your picks</h2>
    <p class="lede" style="margin:0">Copy these and paste them into the chat.</p>
    <button class="copy" id="copy" type="button">Copy my picks</button>
    <p class="status" id="status" role="status"></p>
    <textarea id="result" readonly aria-label="Your picks as text"></textarea>
  </section>
</main>
<script>
const DATA = __DATA__;
const picks = {};
const notes = {};
try { Object.assign(picks, JSON.parse(localStorage.getItem('ear-picks') || '{}')); Object.assign(notes, JSON.parse(localStorage.getItem('ear-notes') || '{}')); } catch (e) {}
const save = () => { try { localStorage.setItem('ear-picks', JSON.stringify(picks)); localStorage.setItem('ear-notes', JSON.stringify(notes)); } catch (e) {} };
const fmt = s => Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');
let current = null;

function render() {
  const host = document.getElementById('samples');
  host.style.display = 'grid'; host.style.gap = '14px';
  DATA.forEach((s, n) => {
    const el = document.createElement('section');
    el.className = 'sample';
    el.setAttribute('aria-label', `Sample ${n + 1}`);
    el.innerHTML = `<header><h2>Apollo ${s.mission}</h2><span class="tape">tape ${s.tape} · from ${s.at}</span></header>
      <div class="versions${s.versions.length === 4 ? ' four' : ''}">${s.versions.map(v => `<button type="button" class="v${v.key === 'journal' ? ' journal' : ''}" data-key="${v.key}"><span class="name">${v.name}</span><span class="detail">${v.detail}</span><span class="noise">background ${v.noise.toFixed(1)} dB</span></button>`).join('')}</div>
      ${s.note ? `<p class="note">${s.note}</p>` : ''}
      <div class="transport"><button type="button" class="play" aria-label="Play">▶</button><input type="range" min="0" max="1" step="0.1" value="0" aria-label="Position"><span class="time">0:00 / 0:00</span></div>
      <div class="picks"><span>Best:</span>${s.versions.map(v => `<label class="pick"><input type="radio" name="pick-${s.id}" value="${v.key}" id="pick-${s.id}-${v.key}"><span>${v.name}</span></label>`).join('')}</div>
      <input class="notes" id="notes-${s.id}" placeholder="Notes (optional): e.g. voices sound watery, hiss still there" value="">`;
    host.appendChild(el);
    const audio = new Audio(); audio.preload = 'metadata';
    let key = s.versions[0].key;
    const buttons = el.querySelectorAll('.v'), play = el.querySelector('.play'), range = el.querySelector('input[type=range]'), time = el.querySelector('.time');
    const mark = () => buttons.forEach(b => b.classList.toggle('playing', b.dataset.key === key && !audio.paused));
    const setSrc = k => { key = k; audio.src = s.versions.find(v => v.key === k).src; };
    setSrc(key);
    buttons.forEach(b => b.addEventListener('click', () => {
      const t = audio.currentTime, wasPlaying = !audio.paused || current !== audio;
      if (current && current !== audio) current.pause();
      setSrc(b.dataset.key);
      audio.addEventListener('loadedmetadata', () => { audio.currentTime = Math.min(t, audio.duration || t); if (wasPlaying) audio.play(); }, { once: true });
      current = audio; mark();
    }));
    play.addEventListener('click', () => {
      if (audio.paused) { if (current && current !== audio) current.pause(); current = audio; audio.play(); } else audio.pause();
    });
    audio.addEventListener('play', () => { play.textContent = '❚❚'; play.setAttribute('aria-label', 'Pause'); mark(); });
    audio.addEventListener('pause', () => { play.textContent = '▶'; play.setAttribute('aria-label', 'Play'); mark(); });
    audio.addEventListener('timeupdate', () => { range.max = audio.duration || 1; range.value = audio.currentTime; time.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration || 0); });
    range.addEventListener('input', () => { audio.currentTime = Number(range.value); });
    el.querySelectorAll('input[type=radio]').forEach(r => {
      if (picks[s.id] === r.value) { r.checked = true; el.classList.add('decided'); }
      r.addEventListener('change', () => { picks[s.id] = r.value; el.classList.add('decided'); save(); summarise(); });
    });
    const note = el.querySelector('.notes');
    note.value = notes[s.id] || '';
    note.addEventListener('input', () => { notes[s.id] = note.value; save(); summarise(); });
  });
}

function summarise() {
  const lines = DATA.map(s => {
    const p = picks[s.id], v = s.versions.find(x => x.key === p);
    return `Apollo ${s.mission} ${s.tape} @${s.at}: ${v ? v.name + ' (' + v.key + ')' : 'not picked'}${notes[s.id] ? ' — ' + notes[s.id] : ''}`;
  });
  document.getElementById('result').value = 'Ear check picks\n' + lines.join('\n');
}

document.getElementById('copy').addEventListener('click', () => {
  const box = document.getElementById('result'), status = document.getElementById('status');
  navigator.clipboard.writeText(box.value).then(() => { status.textContent = 'Copied. Paste it into the chat.'; })
    .catch(() => { box.focus(); box.select(); status.textContent = 'Selected: copy it with your device\'s Copy.'; });
});

render(); summarise();
</script>
'''

if __name__ == '__main__':
    main()
