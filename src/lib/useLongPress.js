import { useRef } from 'react'

const HOLD_MS = 550
const MOVE_TOLERANCE_PX = 10

// Press and hold (or right-click) on an item to act on it. `bind(arg)`
// returns the props for one item and `onLongPress(arg)` receives that
// item's arg; call `consumeClick()` in the item's click handler to skip the
// click that ends a hold.
export function useLongPress(onLongPress) {
  const timer = useRef(null)
  const start = useRef(null)
  const fired = useRef(false)

  function cancel() {
    clearTimeout(timer.current)
    timer.current = null
  }

  function bind(arg) {
    return {
      onPointerDown(e) {
        if (e.button && e.button !== 0) return
        fired.current = false
        start.current = { x: e.clientX, y: e.clientY }
        cancel()
        timer.current = setTimeout(() => {
          fired.current = true
          onLongPress(arg)
        }, HOLD_MS)
      },
      onPointerMove(e) {
        const s = start.current
        if (s && Math.hypot(e.clientX - s.x, e.clientY - s.y) > MOVE_TOLERANCE_PX) cancel()
      },
      onPointerUp: cancel,
      onPointerLeave: cancel,
      onPointerCancel: cancel,
      onContextMenu(e) {
        e.preventDefault()
        // Android also fires contextmenu on a long touch; don't open twice.
        if (fired.current && !timer.current) return
        cancel()
        fired.current = true
        onLongPress(arg)
      },
    }
  }

  function consumeClick() {
    if (!fired.current) return false
    fired.current = false
    return true
  }

  return { bind, consumeClick }
}
