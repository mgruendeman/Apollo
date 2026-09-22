import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'

// HashRouter (not BrowserRouter) because this deploys to GitHub Pages,
// a static host with no server-side rewrite rules — a direct load or
// refresh of a route like /mission/15 would otherwise 404.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>,
)
