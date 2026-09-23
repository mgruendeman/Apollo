import { Link } from 'react-router-dom'
import { astronauts } from '../data/astronauts'
import facts from '../data/astronautFacts.json'
import { missions } from '../data/missions'
import { speakerAvatar } from '../data/speakers'

function Card({ id }) {
  const person = astronauts[id]
  return (
    <Link to={`/astronaut/${id}`} className="astronaut-card">
      <img src={speakerAvatar(id)} alt="" />
      <span className="astronaut-card-name">{person.name}</span>
      <span className="astronaut-card-meta">
        {person.apollo.map((a) => `${a.role === 'CAPCOM' ? 'CAPCOM' : a.role.replace('Command Module Pilot', 'CMP').replace('Lunar Module Pilot', 'LMP')}, ${Number(a.mission)}`).join(' · ')}
      </span>
      {facts[id] && (
        <span className="astronaut-card-service">
          {facts[id].service[0]?.replace(/^civilian scientist-astronaut.*/, 'Civilian scientist')}
          {facts[id].missions.length > 0 && ` · ${facts[id].missions.length} flight${facts[id].missions.length === 1 ? '' : 's'}`}
        </span>
      )}
    </Link>
  )
}

export default function Astronauts() {
  const crewIds = []
  for (const m of missions) {
    for (const name of m.crew) {
      const id = name.split(' ').pop().toLowerCase()
      if (astronauts[id] && !crewIds.includes(id)) crewIds.push(id)
    }
  }
  const capcomIds = Object.keys(astronauts).filter((id) => !crewIds.includes(id))

  return (
    <div className="page">
      <Link to="/" className="back-link">
        ← All missions
      </Link>
      <header className="mission-header">
        <p className="eyebrow">People</p>
        <h1>Astronauts</h1>
        <p className="lede">The crews you hear on these tapes, and the CAPCOMs who talked to them from Houston.</p>
      </header>
      <h3 className="astronaut-group">Crews</h3>
      <div className="astronaut-grid">
        {crewIds.map((id) => (
          <Card key={id} id={id} />
        ))}
      </div>
      <h3 className="astronaut-group">CAPCOMs</h3>
      <div className="astronaut-grid">
        {capcomIds.map((id) => (
          <Card key={id} id={id} />
        ))}
      </div>
    </div>
  )
}
