import { Routes, Route } from 'react-router-dom'
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
import { PlayerProvider } from './audio/PlayerContext'

function App() {
  return (
    <PlayerProvider>
      <ScrollMemory />
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
