import { useCallback, useState } from 'react'
import ReportDialog from './ReportDialog'

// "Report an issue" link that opens the report form, carrying `body` (what
// the reader was looking at) along with whatever they type.
export default function ReportIssueButton({ title, body, children = 'Report an issue' }) {
  const [open, setOpen] = useState(false)
  const close = useCallback(() => setOpen(false), [])
  return (
    <>
      <button type="button" className="report-issue-link" onClick={() => setOpen(true)}>
        {children}
      </button>
      {open && <ReportDialog title={title} context={body || ''} onClose={close} />}
    </>
  )
}
