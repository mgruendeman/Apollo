const REPO_URL = 'https://github.com/mgruendeman/Apollo'

// Opens a pre-filled GitHub issue rather than needing any backend of our
// own to collect reports — this is already a GitHub-hosted project, so
// issues are the natural place for "this transcript/definition looks
// wrong" reports to land where they can actually get fixed.
export default function ReportIssueButton({ title, body, children = 'Report an issue' }) {
  const params = new URLSearchParams({
    title,
    body: body || '',
    labels: 'content-issue',
  })
  const href = `${REPO_URL}/issues/new?${params.toString()}`
  return (
    <a className="report-issue-link" href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  )
}
