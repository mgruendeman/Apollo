import { useCallback, useEffect, useRef, useState } from 'react'

// How long a manual scroll of a transcript pauses auto-scrolling.
const USER_SCROLL_HOLD_MS = 6000

// Keeps the line being spoken centred in a scrolling transcript, pauses that
// for a few seconds after the listener scrolls it themselves, and reports
// when the current line is out of view so a "Current line" button can bring
// it back.
export function useTranscriptScroll(active, resetKey) {
  const listRef = useRef(null)
  const activeRef = useRef(null)
  const userScrolledAt = useRef(0)
  const lastReset = useRef(resetKey)
  const [away, setAway] = useState(false)

  const checkAway = useCallback(() => {
    const list = listRef.current
    const line = activeRef.current
    if (!list || !line) return setAway(false)
    const top = line.offsetTop - list.scrollTop
    setAway(top + line.clientHeight < 0 || top > list.clientHeight)
  }, [])

  const scrollToActive = useCallback((smooth) => {
    const list = listRef.current
    const line = activeRef.current
    if (!list || !line) return
    list.scrollTo({
      top: line.offsetTop - list.clientHeight / 2 + line.clientHeight / 2,
      behavior: smooth ? 'smooth' : 'auto',
    })
  }, [])

  useEffect(() => {
    const fresh = lastReset.current !== resetKey
    lastReset.current = resetKey
    if (fresh || Date.now() - userScrolledAt.current >= USER_SCROLL_HOLD_MS) {
      scrollToActive(!fresh)
    }
    const t = setTimeout(checkAway, 400)
    return () => clearTimeout(t)
  }, [active, resetKey, scrollToActive, checkAway])

  const markUserScroll = useCallback(() => {
    userScrolledAt.current = Date.now()
  }, [])

  const jumpToCurrent = useCallback(() => {
    userScrolledAt.current = 0
    scrollToActive(true)
    setAway(false)
  }, [scrollToActive])

  return {
    listRef,
    activeRef,
    away,
    jumpToCurrent,
    listProps: {
      onWheel: markUserScroll,
      onTouchMove: markUserScroll,
      // Pressing a line (to jump to it or hold to report it) shouldn't have
      // it scroll away underneath the finger.
      onPointerDown: markUserScroll,
      onScroll: checkAway,
    },
  }
}
