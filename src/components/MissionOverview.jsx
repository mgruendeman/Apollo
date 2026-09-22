import { missions } from '../data/missions'
import { speakerAvatar } from '../data/speakers'

const ROLES = ['Commander', 'Command Module Pilot', 'Lunar Module Pilot']

// Orthographic projection onto public/moon-nearside.jpg, which is rendered
// straight-on at 0°N 0°E with no libration, so sites land exactly.
function project(lat, lon) {
  const la = (lat * Math.PI) / 180
  const lo = (lon * Math.PI) / 180
  return { x: 50 + 50 * Math.cos(la) * Math.sin(lo), y: 50 - 50 * Math.sin(la) }
}

function formatCoord(lat, lon) {
  const ns = `${Math.abs(lat).toFixed(3)}°${lat >= 0 ? 'N' : 'S'}`
  const ew = `${Math.abs(lon).toFixed(3)}°${lon >= 0 ? 'E' : 'W'}`
  return `${ns}, ${ew}`
}

function MoonMap({ site, missionId, planned }) {
  const others = missions.filter((m) => m.landingSite && m.id !== missionId)
  const here = project(site.lat, site.lon)
  return (
    <div className="moon-map">
      <img src={`${import.meta.env.BASE_URL}moon-nearside.jpg`} alt="The near side of the Moon" />
      <svg viewBox="0 0 100 100" aria-hidden="true">
        {others.map((m) => {
          const p = project(m.landingSite.lat, m.landingSite.lon)
          return (
            <g key={m.id} className="moon-map-other">
              <circle cx={p.x} cy={p.y} r="0.9" />
              <text
                x={m.landingSite.lon < -20 ? p.x - 1.6 : p.x + 1.6}
                y={p.y + 1}
                textAnchor={m.landingSite.lon < -20 ? 'end' : 'start'}
              >
                {m.number}
              </text>
            </g>
          )
        })}
        <circle className={planned ? 'moon-map-pin is-planned' : 'moon-map-pin'} cx={here.x} cy={here.y} r="2.2" />
      </svg>
    </div>
  )
}

export default function MissionOverview({ mission }) {
  const landed = !!mission.landingSite
  const site = mission.landingSite || mission.plannedSite

  return (
    <section className="mission-overview">
      <div className="crew-row">
        {mission.crew.map((name, i) => {
          const photo = speakerAvatar(name.split(' ').pop())
          return (
            <figure key={name} className="crew-card">
              {photo ? (
                <img src={photo} alt={name} />
              ) : (
                <div className="crew-card-placeholder" />
              )}
              <figcaption>
                <span className="crew-name">{name}</span>
                <span className="crew-role">{ROLES[i]}</span>
                {landed && i !== 1 && <span className="crew-moonwalker">Walked on the Moon</span>}
              </figcaption>
            </figure>
          )
        })}
      </div>

      <dl className="mission-facts">
        <div>
          <dt>Objective</dt>
          <dd>{mission.objective}</dd>
        </div>
        <div>
          <dt>Spacecraft</dt>
          <dd>
            {mission.csmName && <>Command Module <strong>{mission.csmName}</strong></>}
            {mission.csmName && mission.lmName && ' · '}
            {mission.lmName && <>Lunar Module <strong>{mission.lmName}</strong></>}
            {mission.spacecraftNote && <span className="mission-facts-note">{mission.spacecraftNote}</span>}
          </dd>
        </div>
        <div>
          <dt>{landed ? 'Landing site' : site ? 'Planned landing site' : 'Landing'}</dt>
          <dd>
            {site ? (
              <>
                {site.name}
                {landed && <span className="mission-facts-note">{formatCoord(site.lat, site.lon)}</span>}
              </>
            ) : (
              'None: this mission orbited the Moon without landing.'
            )}
          </dd>
        </div>
      </dl>

      {site && <MoonMap site={site} missionId={mission.id} planned={!landed} />}
    </section>
  )
}
