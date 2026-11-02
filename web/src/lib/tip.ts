// Long-press tip for touch screens, where the `title` attribute never shows: `use:tip` on a button
// shows its title above it while the finger rests there, and swallows the click that follows.
const HOLD_MS = 450
const SHOW_MS = 1400

let bubble: HTMLDivElement | undefined

function show(node: HTMLElement, text: string) {
  bubble ??= document.body.appendChild(document.createElement('div'))
  bubble.textContent = text
  bubble.setAttribute('role', 'tooltip')
  bubble.style.cssText =
    'position:fixed;z-index:100;pointer-events:none;padding:0.3rem 0.6rem;border-radius:6px;font-size:0.8rem;' +
    'background:var(--panel);color:var(--text);border:1px solid var(--line);box-shadow:0 2px 10px #0008;white-space:nowrap'
  const box = node.getBoundingClientRect()
  const width = bubble.offsetWidth
  const left = Math.min(Math.max(4, box.left + box.width / 2 - width / 2), innerWidth - width - 4)
  bubble.style.left = `${left}px`
  bubble.style.top = `${Math.max(4, box.top - bubble.offsetHeight - 8)}px`
}

export function tip(node: HTMLElement) {
  let timer: ReturnType<typeof setTimeout> | undefined
  let hide: ReturnType<typeof setTimeout> | undefined
  let shown = false

  const cancel = () => clearTimeout(timer)
  const down = (event: PointerEvent) => {
    if (event.pointerType === 'mouse') return // a mouse has the native tooltip
    shown = false
    timer = setTimeout(() => {
      shown = true
      show(node, node.getAttribute('title') ?? node.getAttribute('aria-label') ?? '')
      clearTimeout(hide)
      hide = setTimeout(() => bubble && (bubble.style.display = 'none'), SHOW_MS)
    }, HOLD_MS)
  }
  const click = (event: MouseEvent) => {
    if (!shown) return
    shown = false
    event.stopImmediatePropagation() // the press was a request for help, not a tap
    event.preventDefault()
  }
  const menu = (event: Event) => shown && event.preventDefault() // no context menu after a long press

  node.addEventListener('pointerdown', down)
  node.addEventListener('pointerup', cancel)
  node.addEventListener('pointerleave', cancel)
  node.addEventListener('pointercancel', cancel)
  node.addEventListener('click', click, true)
  node.addEventListener('contextmenu', menu)
  return {
    destroy() {
      cancel()
      node.removeEventListener('pointerdown', down)
      node.removeEventListener('pointerup', cancel)
      node.removeEventListener('pointerleave', cancel)
      node.removeEventListener('pointercancel', cancel)
      node.removeEventListener('click', click, true)
      node.removeEventListener('contextmenu', menu)
    },
  }
}
