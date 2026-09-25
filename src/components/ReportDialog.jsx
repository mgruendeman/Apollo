import { useEffect, useRef, useState } from 'react'
import { REPORT_ENDPOINT, REPO_URL } from '../config'

// A small form for "this looks wrong" reports: what the listener was looking
// at (`context`) goes along automatically, and they just say what's wrong.
// Sent to REPORT_ENDPOINT when one is configured, otherwise opened as a
// pre-filled GitHub issue.
// With `audio` ({url, at}), a button plays the 12 seconds around the line,
// as often as needed, while the report is written.
export default function ReportDialog({ title, context, audio, onClose }) {
  const playerRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  function replay() {
    const a = playerRef.current
    if (!a) return
    if (!a.paused) {
      a.pause()
      return
    }
    // about 12 s: 3 before the line, 9 after; stopped by time reached or,
    // failing that (a coarse timeupdate), by the clock
    const stopAt = audio.at + 9
    a.currentTime = Math.max(0, audio.at - 3)
    a.ontimeupdate = () => {
      if (a.currentTime >= stopAt) a.pause()
    }
    clearTimeout(a._stop)
    a._stop = setTimeout(() => a.pause(), 12500)
    a.play().catch(() => {})
  }
  const [message, setMessage] = useState('')
  const [contact, setContact] = useState('')
  const [state, setState] = useState('editing') // editing | sending | sent | failed | limit
  const boxRef = useRef(null)

  useEffect(() => {
    boxRef.current?.focus()
    function onKey(e) {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }
    document.addEventListener('keydown', onKey, true)
    return () => document.removeEventListener('keydown', onKey, true)
  }, [onClose])

  async function submit(e) {
    e.preventDefault()
    if (!message.trim()) return
    if (!REPORT_ENDPOINT) {
      const body = `${message.trim()}\n\n---\n${context}`
      const params = new URLSearchParams({ title, body, labels: 'content-issue' })
      window.open(`${REPO_URL}/issues/new?${params}`, '_blank', 'noopener')
      onClose()
      return
    }
    setState('sending')
    try {
      const res = await fetch(REPORT_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ subject: title, message: message.trim(), context, contact, page: window.location.href }),
      })
      setState(res.ok ? 'sent' : res.status === 429 ? 'limit' : 'failed')
    } catch {
      setState('failed')
    }
  }

  return (
    <div className="report-overlay" onClick={onClose} role="presentation">
      <form
        className="report-dialog"
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        role="dialog"
        aria-modal="true"
        aria-label="Report a problem"
      >
        <button type="button" className="glossary-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h3>Report a problem</h3>
        {state === 'sent' ? (
          <>
            <p className="report-done">Thanks — your report was sent.</p>
            <button type="button" className="report-submit" onClick={onClose}>
              Close
            </button>
          </>
        ) : (
          <>
            <p className="report-about">{title}</p>
            {context && <blockquote className="report-context">{context}</blockquote>}
            {audio && (
              <p className="report-replay">
                <audio ref={playerRef} src={audio.url} preload="none" onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} />
                <button type="button" className="report-replay-button" onClick={replay}>
                  {playing ? '❚❚ Stop' : '▶ Play this line'}
                </button>
                <span>a few seconds either side; play it as often as you like</span>
              </p>
            )}
            <label className="report-field">
              What&apos;s wrong?
              <textarea
                ref={boxRef}
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="e.g. the text says 116 but you can hear 176; this line is Aldrin, not Armstrong; or the story behind this moment (with a source)"
                required
              />
            </label>
            {REPORT_ENDPOINT && (
              <label className="report-field">
                Email, if you&apos;d like a reply (optional)
                <input type="email" value={contact} onChange={(e) => setContact(e.target.value)} />
              </label>
            )}
            {state === 'failed' && <p className="report-error">Couldn&apos;t send that. Please try again in a moment.</p>}
            {state === 'limit' && (
              <p className="report-error">That&apos;s the most reports we take from one connection in a day. Thank you! Please send the rest tomorrow.</p>
            )}
            <button type="submit" className="report-submit" disabled={state === 'sending' || !message.trim()}>
              {state === 'sending' ? 'Sending…' : REPORT_ENDPOINT ? 'Send report' : 'Continue on GitHub'}
            </button>
          </>
        )}
      </form>
    </div>
  )
}
