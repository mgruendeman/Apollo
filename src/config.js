// Where "report a problem" forms are sent. Set VITE_REPORT_ENDPOINT at build
// time to a form service that accepts a JSON POST (for example a Formspree
// form URL, https://formspree.io/f/<id>). Left empty, reports open as a
// pre-filled GitHub issue instead.
export const REPORT_ENDPOINT = import.meta.env.VITE_REPORT_ENDPOINT || ''

export const REPO_URL = 'https://github.com/mgruendeman/Apollo'
