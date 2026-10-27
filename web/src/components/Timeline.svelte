<script lang="ts">
  // The timeline: waveform (peaks from the server), one draggable region per cue, the cuts and
  // the in/out mark. wavesurfer.js draws it and follows the <video>. Ctrl + wheel zooms around
  // the pointer; edges snap to nearby cue edges, words, cuts and the playhead (settings.json: snapPx).
  // The playhead has two modes: a draggable arrow on the line (pointer devices), or fixed in the centre while
  // the timeline scrolls under it, with empty space before the start (touch screens).
  import WaveSurfer from 'wavesurfer.js'
  import RegionsPlugin, { type Region } from 'wavesurfer.js/dist/plugins/regions.esm.js'
  import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js'
  import { onDestroy, onMount } from 'svelte'
  import { loadPeaks } from '../lib/api'
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { cutsOf, snap, snapPoints } from '../lib/timeline'
  import { settings } from '../lib/settings'
  import { ui } from '../lib/ui.svelte'

  const SNAP_PX = settings.snapPx
  // touch screens: the playhead stays in the centre and the timeline slides under it (like mobile editors)
  const center = settings.playhead === 'center' || (settings.playhead === 'auto' && matchMedia('(pointer: coarse)').matches)
  // subtitles are orange (as in CapCut); cuts are grey-blue and the in/out mark is blue, so none is mistaken for a subtitle
  const COLOR = 'rgba(232, 118, 30, 0.6)'
  const CURRENT = 'rgba(255, 190, 60, 0.85)'
  const SELECTED = 'rgba(255, 150, 70, 0.95)'
  const CUT = 'rgba(70, 80, 110, 0.75)'
  const MARK = 'rgba(70, 160, 255, 0.35)'

  let container: HTMLDivElement
  let ws: WaveSurfer | undefined
  let regions: ReturnType<typeof RegionsPlugin.create> | undefined
  let ready = $state(false)
  let pxPerSec = 60
  let minPx = 4
  const cueRegions: Region[] = []
  let overlays: Region[] = [] // cuts and the mark: rebuilt when their signature changes
  let overlayKey = ''
  let dragPoints: number[] | null = null // snap targets, built once per drag
  let raw: { start: number; end: number; drawnStart: number; drawnEnd: number } | null = null // where the pointer put the dragged block
  let guide: Region | undefined // the line that shows what the edge is stuck to
  let guideAt: number | null = null

  const project = $derived(editor.project!)

  let frame = 0
  let stage: HTMLDivElement
  let head: HTMLDivElement // the playhead: an arrow above the waveform and a line over the blocks (outside wavesurfer's shadow DOM)
  let arrow: HTMLDivElement
  let scroller: HTMLElement
  let wrap: HTMLElement // wavesurfer's wide inner element

  /**
   * Position the playhead every frame (the time is read from the <video>, ADR-015).
   * Arrow mode: it sits where the time is and the arrow can be dragged.
   * Centred mode: it stays in the middle; the timeline scrolls under it, and a shift to the right leaves
   * empty space before the start (the waveform is only moved, never re-laid out, so wavesurfer still draws all of it).
   */
  function follow() {
    const view = scroller.clientWidth
    const at = player.time() * pxPerSec
    let x = at - scroller.scrollLeft
    if (center) {
      scroller.scrollLeft = Math.max(0, at - view / 2)
      const shift = Math.max(0, view / 2 - at)
      wrap.style.transform = `translateX(${shift}px)`
      x = view / 2
    }
    head.style.transform = `translateX(${x}px)`
    head.style.visibility = x < -1 || x > view + 1 ? 'hidden' : 'visible'
    frame = requestAnimationFrame(follow)
  }

  function setupPlayhead() {
    wrap = ws!.getWrapper()
    scroller = wrap.parentElement!
    follow()
    if (center) {
      // our own pan: a drag on the timeline moves the video time (touch scrolling is off, so the playhead stays put)
      scroller.style.touchAction = 'none'
      container.addEventListener('pointerdown', (event) => {
        const picked = `c${editor.selected}`
        if (editor.selected >= 0 && event.composedPath().some((n) => (n as HTMLElement).getAttribute?.('part')?.split(' ').includes(picked))) return // dragging the selected block
        let lastX = event.clientX
        const move = (e: PointerEvent) => {
          player.seek(Math.min(project.duration, Math.max(0, player.time() - (e.clientX - lastX) / pxPerSec)))
          lastX = e.clientX
        }
        const stop = () => {
          window.removeEventListener('pointermove', move)
          window.removeEventListener('pointerup', stop)
        }
        window.addEventListener('pointermove', move)
        window.addEventListener('pointerup', stop)
      })
    } else {
      arrow.addEventListener('pointerdown', (event) => {
        event.stopPropagation()
        arrow.setPointerCapture(event.pointerId)
        const move = (e: PointerEvent) => {
          const box = container.getBoundingClientRect()
          if (e.clientX > box.right - 24) scroller.scrollLeft += 14 // near an edge: keep the timeline moving
          else if (e.clientX < box.left + 24) scroller.scrollLeft -= 14
          const at = (e.clientX - box.left + scroller.scrollLeft) / pxPerSec
          player.seek(Math.min(project.duration, Math.max(0, at)))
        }
        const stop = () => {
          arrow.removeEventListener('pointermove', move)
          arrow.removeEventListener('pointerup', stop)
        }
        arrow.addEventListener('pointermove', move)
        arrow.addEventListener('pointerup', stop)
      })
    }
  }

  onMount(async () => {
    const peaks = await loadPeaks()
    minPx = Math.max(1, container.clientWidth / peaks.duration)
    pxPerSec = Math.max(minPx, settings.zoomStartPxPerSec)
    regions = RegionsPlugin.create()
    ws = WaveSurfer.create({
      container,
      media: player.video!,
      height: 110,
      minPxPerSec: pxPerSec,
      waveColor: '#5fa57a',
      progressColor: '#8fd3a8',
      cursorColor: '#ffd23f',
      cursorWidth: 0,
      autoCenter: !center,
      autoScroll: !center,
      peaks: [peaks.peaks],
      duration: peaks.duration,
      plugins: [regions, TimelinePlugin.create()],
    })
    ws.on('zoom', (px) => (pxPerSec = px))
    regions.on('region-update', onDragging)
    regions.on('region-updated', onUpdated)
    regions.on('region-clicked', (region: Region, event: MouseEvent) => {
      event.stopPropagation()
      if (!region.id.startsWith('c')) return
      editor.selected = Number(region.id.slice(1))
      player.seek(region.start)
    })
    // double-click: select the block and jump to its text
    regions.on('region-double-clicked', (region: Region) => {
      if (!region.id.startsWith('c')) return
      editor.selected = Number(region.id.slice(1))
      editor.focusText++
    })
    ws.on('click', () => (editor.selected = -1)) // a click on the empty waveform clears the selection (regions stop their own clicks)
    container.addEventListener('wheel', onWheel, { passive: false })
    await new Promise<void>((done) => ws!.once('ready', () => done()))
    ready = true
    setupPlayhead()
  })

  onDestroy(() => {
    cancelAnimationFrame(frame)
    container?.removeEventListener('wheel', onWheel)
    ws?.destroy()
  })

  // Re-draw regions when the project (or the current cue) changes: update in place, add or remove the difference.
  $effect(() => {
    if (!ready || !regions) return
    const cues = project.cues
    cues.forEach((cue, i) => {
      const picked = i === editor.selected // only the selected block can be dragged or resized, so scrolling by touch never moves one
      const options = { start: cue.start, end: cue.end, content: cue.text, color: picked ? SELECTED : i === editor.current ? CURRENT : COLOR }
      const region = cueRegions[i]
      if (!region) {
        cueRegions[i] = regions!.addRegion({ id: `c${i}`, ...options, drag: picked, resize: picked })
        grip(cueRegions[i], picked)
      } else if (
        region.start !== options.start || region.end !== options.end ||
        region.content?.textContent !== cue.text || region.color !== options.color ||
        region.drag !== picked || region.resize !== picked
      ) {
        region.setOptions({ ...options, drag: picked, resize: picked })
        grip(region, picked)
      }
    })
    while (cueRegions.length > cues.length) cueRegions.pop()!.remove()
  })

  $effect(() => {
    if (!ready || !regions) return
    const cuts = cutsOf(project.keep, project.duration)
    const mark = editor.markIn === null ? null : [editor.markIn, editor.markOut ?? editor.markIn]
    const key = JSON.stringify([cuts, mark])
    if (key === overlayKey) return
    overlayKey = key
    overlays.forEach((r) => r.remove())
    overlays = cuts.map(([start, end]) =>
      regions!.addRegion({ id: `x${start}`, start, end, color: CUT, drag: false, resize: false }),
    )
    if (mark) {
      const [a, b] = mark
      overlays.push(regions!.addRegion({ id: 'mark', start: Math.min(a, b), end: Math.max(a, b) + 0.01, color: MARK, drag: false, resize: false }))
    }
  })

  // A block that is not selected leaves touch gestures to the page (scrolling); the selected one takes them.
  function grip(region: Region, picked: boolean) {
    if (region.element) region.element.style.touchAction = picked ? 'none' : 'pan-x pan-y'
  }

  // Snap targets for dragging cue `i`: other cues' edges, its own words, kept-range edges, the playhead.
  function targets(i: number): number[] {
    return snapPoints([
      player.time(),
      ...project.cues.flatMap((c, j) => (j === i ? (c.words ?? []).flatMap((w) => [w.start, w.end]) : [c.start, c.end])),
      ...project.keep.flat(),
    ])
  }

  /**
   * Where a block should sit after snapping, from where the pointer really put it (`start`, `end`),
   * and which time it stuck to (null: nothing near).
   */
  function snapped(i: number, start: number, end: number, side?: string) {
    const points = (dragPoints ??= targets(i))
    const threshold = SNAP_PX / pxPerSec
    let target: number | null = null
    if (side === 'start') {
      const to = snap(start, points, threshold)
      if (to !== start) target = to
      start = to
    } else if (side === 'end') {
      const to = snap(end, points, threshold)
      if (to !== end) target = to
      end = to
    } else {
      // dragging the whole block: the closer of the two edges decides, the length stays
      const a = snap(start, points, threshold) - start
      const b = snap(end, points, threshold) - end
      const shift = a !== 0 && (b === 0 || Math.abs(a) <= Math.abs(b)) ? a : b
      if (shift !== 0) target = (shift === a ? start : end) + shift
      start += shift
      end += shift
    }
    return { start, end, target }
  }

  // The guide line: a thin marker at the time the edge is stuck to.
  function showGuide(time: number | null) {
    if (time === guideAt) return
    guide?.remove()
    guide = undefined
    guideAt = time
    if (time !== null) guide = regions?.addRegion({ id: 'guide', start: time, end: time, color: '#ffffff', drag: false, resize: false })
  }

  // wavesurfer moves a block by the pointer's change since the last event. Snapping moves the block
  // too, so we keep the position the pointer asked for (`raw`) apart from where the block is drawn:
  // the block sticks to a target while the pointer is near it and follows again once it leaves.
  function onDragging(region: Region, side?: string) {
    if (!region.id.startsWith('c')) return
    const i = Number(region.id.slice(1))
    const cue = project.cues[i]
    if (!cue) return
    const track = (raw ??= { start: cue.start, end: cue.end, drawnStart: cue.start, drawnEnd: cue.end })
    track.start += region.start - track.drawnStart
    track.end += region.end - track.drawnEnd
    const result = ui.snap ? snapped(i, track.start, track.end, side) : { start: region.start, end: region.end, target: null }
    track.drawnStart = result.start
    track.drawnEnd = result.end
    if (result.start !== region.start || result.end !== region.end) {
      region.setOptions({ start: result.start, end: result.end })
    }
    showGuide(result.target)
  }

  // Released: store the new times in the project.
  function onUpdated(region: Region) {
    showGuide(null)
    if (!region.id.startsWith('c')) return
    const i = Number(region.id.slice(1))
    const cue = project.cues[i]
    dragPoints = null
    raw = null
    if (!cue) return
    const movedStart = Math.abs(region.start - cue.start) > 1e-3
    const movedEnd = Math.abs(region.end - cue.end) > 1e-3
    if (!movedStart && !movedEnd) return // our own re-draw
    editor.setTimes(i, region.start, region.end)
    // keep the region where the project has it (the project may have clamped or sorted)
    region.setOptions({ start: project.cues[i]?.start ?? region.start, end: project.cues[i]?.end ?? region.end })
  }

  function setZoom(px: number, anchorX?: number) {
    if (!ws) return
    const x = anchorX ?? container.clientWidth / 2
    const timeAt = (ws.getScroll() + x) / pxPerSec
    pxPerSec = Math.min(settings.zoomMaxPxPerSec, Math.max(minPx, px))
    ws.zoom(pxPerSec)
    if (!center) ws.setScroll(Math.max(0, timeAt * pxPerSec - x)) // centred mode follows the playhead instead
  }

  function onWheel(event: WheelEvent) {
    if (!event.ctrlKey && !event.metaKey) return
    event.preventDefault()
    const box = container.getBoundingClientRect()
    setZoom(pxPerSec * (event.deltaY < 0 ? 1.2 : 1 / 1.2), event.clientX - box.left)
  }
</script>

<section>
  <div class="bar">
    <h2>{t('timeline.title')}</h2>
    <span class="spacer"></span>
    <button onclick={() => setZoom(pxPerSec / 1.5)} title={t('timeline.zoom_out')}>−</button>
    <button onclick={() => setZoom(minPx)}>{t('timeline.fit')}</button>
    <button onclick={() => setZoom(pxPerSec * 1.5)} title={t('timeline.zoom_in')}>+</button>
  </div>
  <div class="stage" bind:this={stage}>
    <div class="wave" bind:this={container}></div>
    <div class="head" class:center bind:this={head}>
      <div class="arrow" bind:this={arrow}></div>
      <div class="line"></div>
    </div>
  </div>
  {#if !ready}<p class="muted">{t('loading')}</p>{/if}
</section>

<style>
  .bar { display: flex; gap: 0.5rem; align-items: baseline; }
  .bar h2 { margin: 0 0.5rem 0.4rem 0; }
  .spacer { flex: 1; }
  .stage { position: relative; padding-top: 16px; margin-top: 0.2rem; }
  .wave { background: var(--bg); border-radius: 6px; overflow: hidden; }
  .head { position: absolute; top: 0; bottom: 0; left: 0; width: 0; z-index: 10; pointer-events: none; }
  .arrow { position: absolute; top: 0; left: -10px; width: 20px; height: 17px; background: #ffd23f; clip-path: polygon(0 0, 100% 0, 50% 100%); pointer-events: auto; cursor: ew-resize; touch-action: none; }
  .head.center .arrow { pointer-events: none; cursor: default; }
  .line { position: absolute; top: 16px; bottom: 0; left: -1px; width: 2px; background: #ffd23f; }
</style>
