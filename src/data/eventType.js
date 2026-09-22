// Classifies a timeline chapter as a major milestone, a routine/rest
// stretch, or ordinary content — a narrative aid so the full clip-by-clip
// timeline reads more like an event list than an undifferentiated wall of
// entries. Matched against the chapter's own source-page title.

const MAJOR_RE =
  /\blaunch\b|lift-?off|translunar injection|\btli\b|transposition|docking|lunar orbit insertion|\bloi\b|descent orbit insertion|\bdoi\b|powered descent|landing\b|has landed|first steps|one small step|\beva-?1\b|\beva-?2\b|\beva-?3\b|ascent from|rendezvous|trans-earth injection|\btei\b|entry (and|&) splashdown|splashdown|genesis rock|hadley rille|big muley|snoopy|sce to aux|we've had a problem|farewell/i

const REST_RE = /\b(sleep|rest period|resting|wake-?up|waking|crew rest)\b/i

export function classifyEventType(label) {
  if (REST_RE.test(label)) return 'rest'
  if (MAJOR_RE.test(label)) return 'major'
  return 'routine'
}

export const EVENT_TYPE_META = {
  major: { icon: '★', className: 'is-major' },
  rest: { icon: '☾', className: 'is-rest' },
  routine: { icon: '', className: '' },
}
