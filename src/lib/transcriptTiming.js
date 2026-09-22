// The journals only timestamp radio calls; Mission Control commentary and
// other untimed lines inherit the previous line's GET, so several lines can
// share one timestamp and would all light up at once, ahead of the audio.
// Spread each such run evenly across the gap until the next timestamp.
export function effectiveOffsets(lines) {
  const out = lines.map((l) => l.offsetSeconds)
  let i = 0
  while (i < lines.length) {
    let j = i + 1
    while (j < lines.length && lines[j].offsetSeconds === lines[i].offsetSeconds) j++
    const count = j - i
    if (count > 1) {
      const start = lines[i].offsetSeconds
      const next = j < lines.length ? lines[j].offsetSeconds : null
      const end = next != null && next > start ? next : start + count * 4
      for (let k = 1; k < count; k++) out[i + k] = start + ((end - start) * k) / count
    }
    i = j
  }
  return out
}

export function activeLineIndex(offsets, currentTime) {
  let idx = -1
  for (let i = 0; i < offsets.length; i++) {
    if (offsets[i] <= currentTime) idx = i
    else break
  }
  return idx
}
