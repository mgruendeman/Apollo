import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Mission from './pages/Mission'
import Glossary from './pages/Glossary'
import GlossaryDetail from './pages/GlossaryDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/mission/:id" element={<Mission />} />
      <Route path="/glossary" element={<Glossary />} />
      <Route path="/glossary/:id" element={<GlossaryDetail />} />
    </Routes>
  )
}

export default App
