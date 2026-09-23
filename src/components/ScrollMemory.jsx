import { useEffect, useLayoutEffect } from 'react'
import { useLocation, useNavigationType } from 'react-router-dom'

const KEY = 'scroll-memory'

function load() {
  try {
    return JSON.parse(sessionStorage.getItem(KEY)) || {}
  } catch {
    return {}
  }
}

function save(map) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(map))
  } catch {
    // Private mode or storage full: going back just starts at the top.
  }
}

// Going back returns to where you were on that page; following a link
// starts the new page at the top. With ?focus=<id> the page scrolls to
// that element (e.g. one glossary entry).
export default function ScrollMemory() {
  const location = useLocation()
  const navType = useNavigationType()

  // Remember this page's scroll position as the reader moves around it.
  useEffect(() => {
    let frame = 0
    function onScroll() {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const map = load()
        map[location.key] = window.scrollY
        save(map)
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', onScroll)
    }
  }, [location.key])

  useLayoutEffect(() => {
    const focus = new URLSearchParams(location.search).get('focus')
    const target = navType === 'POP' ? load()[location.key] : undefined
    if (!focus && target === undefined) {
      if (navType !== 'POP') window.scrollTo(0, 0)
      return
    }
    // Pages that load their data after rendering (a mission's clips) aren't
    // tall enough yet, so keep trying for a couple of seconds.
    const started = performance.now()
    let frame = 0
    function attempt() {
      if (focus) {
        const el = document.getElementById(focus)
        if (el) return el.scrollIntoView({ block: 'start' })
      } else if (document.documentElement.scrollHeight - window.innerHeight >= target) {
        return window.scrollTo(0, target)
      }
      if (performance.now() - started < 2500) frame = requestAnimationFrame(attempt)
      else if (!focus) window.scrollTo(0, target)
    }
    attempt()
    return () => cancelAnimationFrame(frame)
  }, [location.key, location.search, navType])

  return null
}
