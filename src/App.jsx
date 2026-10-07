import { useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { track } from './lib/track'
import Home from './pages/Home'
import Mission from './pages/Mission'
import Glossary from './pages/Glossary'
import GlossaryDetail from './pages/GlossaryDetail'
import Astronauts from './pages/Astronauts'
import Astronaut from './pages/Astronaut'
import Guide from './pages/Guide'
import Contact from './pages/Contact'
import NowPlayingBar from './components/NowPlayingBar'
import ScrollMemory from './components/ScrollMemory'
import ConstructionBar from './components/ConstructionBar'
import SiteHeader from './components/SiteHeader'
import { PlayerProvider } from './audio/PlayerContext'

// a page view for the site's statistics: the route's shape, with the mission or entry it names
function PageViews() {
  const { pathname } = useLocation()
  useEffect(() => {
    const m = pathname.match(/^\/mission\/(\d+)/)
    track('page', m ? m[1] : '', pathname.replace(/^\/(mission|glossary|astronaut)\/[^/]+.*/, '/$1/:id') || '/')
    if (m) track('mission', m[1])
  }, [pathname])
  return null
}

function App() {
  return (
    <PlayerProvider>
      <ScrollMemory />
      <PageViews />
      <ConstructionBar />
      <SiteHeader />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/mission/:id" element={<Mission />} />
        <Route path="/glossary" element={<Glossary />} />
        <Route path="/glossary/:id" element={<GlossaryDetail />} />
        <Route path="/astronauts" element={<Astronauts />} />
        <Route path="/astronaut/:id" element={<Astronaut />} />
        <Route path="/guide" element={<Guide />} />
        <Route path="/contact" element={<Contact />} />
      </Routes>
      <NowPlayingBar />
    </PlayerProvider>
  )
}

export default App
