import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import logoSmall from '../assets/logo/apollo-rewind-small.webp'
import { DESIGNS, setGlobeArt, useDesign, useGlobeArt } from '../lib/design'
import { GLOBE_ART } from '../data/globeArt'

// On every page: the logo (home has it large already) and the Design menu.
export default function SiteHeader() {
  const { pathname } = useLocation()
  const [design, setDesign] = useDesign()
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)
  const art = { earth: useGlobeArt('earth').id, moon: useGlobeArt('moon').id }

  useEffect(() => {
    if (!open) return undefined
    const away = (e) => {
      if (!menuRef.current?.contains(e.target)) setOpen(false)
    }
    const esc = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', away)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('pointerdown', away)
      document.removeEventListener('keydown', esc)
    }
  }, [open])

  return (
    <header className="site-header">
      {pathname !== '/' && (
        <Link to="/" className="site-header-logo" aria-label="Apollo Rewind: all missions">
          <img src={logoSmall} alt="Apollo Rewind" />
        </Link>
      )}
      <div className="design-menu" ref={menuRef}>
        <button type="button" aria-haspopup="true" aria-expanded={open} onClick={() => setOpen(!open)}>
          Design ▾
        </button>
        {open && (
          <div className="design-options">
            <p className="design-group" id="design-colors">Colors</p>
            <div role="radiogroup" aria-labelledby="design-colors" className="design-group-options">
            {DESIGNS.map((d) => (
              <button key={d.id} type="button" role="radio" aria-checked={design === d.id} onClick={() => setDesign(d.id)}>
                <span className="design-swatch" aria-hidden="true">
                  {d.swatch.map((c) => (
                    <span key={c} style={{ background: c }} />
                  ))}
                </span>
                <span>
                  {d.label}
                  <small>{d.note}</small>
                </span>
              </button>
            ))}
            </div>
            {['earth', 'moon'].map((kind) => (
              <div key={kind}>
                <p className="design-group" id={`design-${kind}`}>
                  {kind === 'earth' ? 'Earth' : 'Moon'} in the mission diagram
                </p>
                <div role="radiogroup" aria-labelledby={`design-${kind}`} className="design-art">
                  {GLOBE_ART[kind].map((a) => (
                    <button key={a.id} type="button" role="radio" aria-checked={art[kind] === a.id} onClick={() => setGlobeArt(kind, a.id)}>
                      <img src={a.sprite[0]} alt="" width="40" height="40" />
                      {a.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </header>
  )
}
