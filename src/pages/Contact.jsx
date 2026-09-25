import { useState } from 'react'
import { Link } from 'react-router-dom'
import { REPORT_ENDPOINT, REPO_URL } from '../config'

const KINDS = [
  ['suggestion', 'A suggestion or idea'],
  ['question', 'A question'],
  ['problem', 'Something not working'],
  ['other', 'Something else'],
]

// General contact and suggestions. Goes to the same inbox as line reports,
// marked "Contact:" so it's kept apart from transcript fixes.
export default function Contact() {
  const [kind, setKind] = useState('suggestion')
  const [message, setMessage] = useState('')
  const [contact, setContact] = useState('')
  const [state, setState] = useState('editing') // editing | sending | sent | failed | limit
  const label = KINDS.find(([k]) => k === kind)[1]

  async function submit(e) {
    e.preventDefault()
    if (!message.trim()) return
    if (!REPORT_ENDPOINT) {
      const params = new URLSearchParams({ title: `${label}`, body: message.trim(), labels: 'feedback' })
      window.open(`${REPO_URL}/issues/new?${params}`, '_blank', 'noopener')
      return
    }
    setState('sending')
    try {
      const res = await fetch(REPORT_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ subject: `Contact: ${label}`, message: message.trim(), context: `Kind: ${kind}`, contact, page: window.location.href }),
      })
      setState(res.ok ? 'sent' : res.status === 429 ? 'limit' : 'failed')
    } catch {
      setState('failed')
    }
  }

  return (
    <div className="page contact">
      <Link to="/" className="back-link">
        ← All missions
      </Link>
      <header className="mission-header">
        <p className="eyebrow">Contact</p>
        <h1>Suggestions and questions</h1>
        <p className="lede">
          Ideas for the site, questions about a mission, or something that isn&apos;t working: send it here. To fix a
          line of a transcript, it&apos;s quickest to press and hold that line (<Link to="/guide">how</Link>).
        </p>
      </header>

      {state === 'sent' ? (
        <div className="contact-done">
          <p>Thanks, that&apos;s been sent.</p>
          <button
            type="button"
            className="report-submit"
            onClick={() => {
              setMessage('')
              setState('editing')
            }}
          >
            Send another
          </button>
        </div>
      ) : (
        <form className="contact-form" onSubmit={submit}>
          <fieldset className="contact-kinds">
            <legend>What is it?</legend>
            {KINDS.map(([k, text]) => (
              <label key={k}>
                <input type="radio" name="kind" value={k} checked={kind === k} onChange={() => setKind(k)} /> {text}
              </label>
            ))}
          </fieldset>
          <label className="report-field">
            Your message
            <textarea rows={6} value={message} onChange={(e) => setMessage(e.target.value)} required />
          </label>
          {REPORT_ENDPOINT && (
            <label className="report-field">
              Email, if you&apos;d like a reply (optional)
              <input type="email" value={contact} onChange={(e) => setContact(e.target.value)} />
            </label>
          )}
          {state === 'failed' && <p className="report-error">Couldn&apos;t send that. Please try again in a moment.</p>}
          {state === 'limit' && (
            <p className="report-error">That&apos;s the most messages we take from one connection in a day. Please try again tomorrow.</p>
          )}
          <button type="submit" className="report-submit" disabled={state === 'sending' || !message.trim()}>
            {state === 'sending' ? 'Sending…' : REPORT_ENDPOINT ? 'Send' : 'Continue on GitHub'}
          </button>
        </form>
      )}
    </div>
  )
}
