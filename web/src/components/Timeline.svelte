<script lang="ts">
  // The timeline: waveform (peaks from the server), one draggable region per cue, the cuts and
  // the in/out mark. wavesurfer.js draws it and follows the <video>. Ctrl + wheel zooms around
  // the pointer; edges snap to nearby cue edges, words, cuts and the playhead (8 px).
  import WaveSurfer from 'wavesurfer.js'
  import RegionsPlugin, { type Region } from 'wavesurfer.js/dist/plugins/regions.esm.js'
  import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js'
  import { onDestroy, onMount } from 'svelte'
  import { loadPeaks } from '../lib/api'
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { cutsOf, snap, snapPoints } from '../lib/timeline'

  const SNAP_PX = 8
  const COLOR = 'rgba(110, 86, 207, 0.55)'
  const CURRENT = 'rgba(255, 210, 63, 0.6)'
  const CUT = 'rgba(229, 72, 77, 0.5)'
  const MARK = 'rgba(255, 210, 63, 0.25)'

  let container: HTMLDivElement
  let ws: WaveSurfer | undefined
  let regions: ReturnType<typeof RegionsPlugin.create> | undefined
  let ready = $state(false)
  let pxPerSec = 60
  let minPx = 4
  const cueRegions: Region[] = []
  let overlays: Region[] = [] // cuts and the mark: rebuilt when their signature changes
  let overlayKey = ''

  const project = $derived(editor.project!)

  onMount(async () => {
    const peaks = await loadPeaks()
    minPx = Math.max(1, container.clientWidth / peaks.duration)
    pxPerSec = Math.max(minPx, 60)
    regions = RegionsPlugin.create()
    ws = WaveSurfer.create({
      container,
      media: player.video!,
      height: 110,
      minPxPerSec: pxPerSec,
      waveColor: '#5fa57a',
      progressColor: '#8fd3a8',
      cursorColor: '#ffffff',
      peaks: [peaks.peaks],
      duration: peaks.duration,
      plugins: [regions, TimelinePlugin.create()],
    })
    ws.on('zoom', (px) => (pxPerSec = px))
    regions.on('region-updated', onUpdated)
    regions.on('region-clicked', (region: Region, event: MouseEvent) => {
      event.stopPropagation()
      if (region.id.startsWith('c')) player.seek(region.start)
    })
    regions.on('region-double-clicked', (region: Region) => {
      if (region.id.startsWith('c')) editor.split(Number(region.id.slice(1)), player.time())
    })
    container.addEventListener('wheel', onWheel, { passive: false })
    await new Promise<void>((done) => ws!.once('ready', () => done()))
    ready = true
  })

  onDestroy(() => {
    container?.removeEventListener('wheel', onWheel)
    ws?.destroy()
  })

  // Re-draw regions when the project (or the current cue) changes: update in place, add or remove the difference.
  $effect(() => {
    if (!ready || !regions) return
    const cues = project.cues
    cues.forEach((cue, i) => {
      const options = { start: cue.start, end: cue.end, content: cue.text, color: i === editor.current ? CURRENT : COLOR }
      const region = cueRegions[i]
      if (!region) {
        cueRegions[i] = regions!.addRegion({ id: `c${i}`, ...options, drag: true, resize: true })
      } else if (
        region.start !== options.start || region.end !== options.end ||
        region.content?.textContent !== cue.text || region.color !== options.color
      ) {
        region.setOptions(options)
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

  // A region was dragged or resized: snap the moved edge(s) and store the new times.
  function onUpdated(region: Region) {
    if (!region.id.startsWith('c')) return
    const i = Number(region.id.slice(1))
    const cue = project.cues[i]
    if (!cue) return
    const movedStart = Math.abs(region.start - cue.start) > 1e-3
    const movedEnd = Math.abs(region.end - cue.end) > 1e-3
    if (!movedStart && !movedEnd) return // our own re-draw
    const threshold = SNAP_PX / pxPerSec
    const points = snapPoints([
      player.time(),
      ...project.cues.flatMap((c, j) => (j === i ? (c.words ?? []).flatMap((w) => [w.start, w.end]) : [c.start, c.end])),
      ...project.keep.flat(),
    ])
    let [start, end] = [region.start, region.end]
    if (movedStart && movedEnd) {
      // dragged whole: snap whichever edge is closer to a target, keep the length
      const a = snap(start, points, threshold) - start
      const b = snap(end, points, threshold) - end
      const shift = a !== 0 && (b === 0 || Math.abs(a) <= Math.abs(b)) ? a : b
      start += shift
      end += shift
    } else if (movedStart) start = snap(start, points, threshold)
    else end = snap(end, points, threshold)
    editor.setTimes(i, start, end)
    // If snapping changed nothing in the project (same values), put the region back where the project has it.
    region.setOptions({ start: project.cues[i]?.start ?? start, end: project.cues[i]?.end ?? end })
  }

  function setZoom(px: number, anchorX?: number) {
    if (!ws) return
    const x = anchorX ?? container.clientWidth / 2
    const timeAt = (ws.getScroll() + x) / pxPerSec
    pxPerSec = Math.min(1000, Math.max(minPx, px))
    ws.zoom(pxPerSec)
    ws.setScroll(Math.max(0, timeAt * pxPerSec - x))
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
  <p class="muted hint">{t('timeline.hint')}</p>
  <div class="wave" bind:this={container}></div>
  {#if !ready}<p class="muted">{t('loading')}</p>{/if}
</section>

<style>
  .bar { display: flex; gap: 0.5rem; align-items: baseline; }
  .bar h2 { margin: 0 0.5rem 0.4rem 0; }
  .spacer { flex: 1; }
  .hint { margin: 0; }
  .wave { margin-top: 0.4rem; background: var(--bg); border-radius: 6px; }
</style>
