<script lang="ts">
  // The video with the exact subtitle preview (JASSUB = libass in WebAssembly, the same
  // renderer FFmpeg uses on export), cut skipping and the in/out marks.
  import JASSUB from 'jassub'
  import { onDestroy, onMount } from 'svelte'
  import { previewAss } from '../lib/api'
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import shortcuts from '../lib/shortcuts.json'
  import { clock, outputDuration, skipTarget } from '../lib/timeline'

  let video: HTMLVideoElement
  let clockEl: HTMLSpanElement
  let subs: JASSUB | undefined
  let frame = 0

  let { font }: { font: string } = $props()

  const project = $derived(editor.project!)

  onMount(async () => {
    player.video = video
    // libass finds fonts by lowercase family name; without the file it uses JASSUB's bundled font.
    const family = font.toLowerCase()
    const hasFont = (await fetch('/api/font', { method: 'HEAD' })).ok
    subs = new JASSUB({
      video,
      subContent: await previewAss(),
      // `fonts` loads it up front, so the very first frame is drawn with it.
      ...(hasFont ? { fonts: ['/api/font'], availableFonts: { [family]: '/api/font' }, defaultFont: family } : {}),
      queryFonts: false,
    })
    editor.onPreview = async (ass) => {
      await subs?.ready
      await subs?.renderer.setTrack(ass)
      repaint()
    }
    video.addEventListener('seeked', repaint)
    frame = video.requestVideoFrameCallback(tick)
  })

  onDestroy(() => {
    video?.cancelVideoFrameCallback(frame)
    subs?.destroy()
    player.video = null
  })

  // While paused, the browser may not report new frames after a seek; draw that time ourselves.
  async function repaint() {
    await subs?.ready
    if (!subs || !video.paused) return
    const frameInfo = { expectedDisplayTime: performance.now(), mediaTime: video.currentTime }
    subs.manualRender({ ...frameInfo, width: video.videoWidth, height: video.videoHeight }, true)
  }

  // Runs once per video frame: skip cut parts, track the current cue.
  // It writes to the DOM directly instead of reactive state (ADR-015 player rule).
  function tick() {
    const time = video.currentTime
    const jump = video.paused ? null : skipTarget(project.keep, time)
    if (jump === Infinity) video.pause()
    else if (jump !== null) video.currentTime = jump
    clockEl.textContent = clock(time)
    const index = project.cues.findIndex((c) => c.start <= time && time < c.end)
    if (index !== editor.current) editor.current = index
    frame = video.requestVideoFrameCallback(tick)
  }

  function togglePlay() {
    if (video.paused) {
      const jump = skipTarget(project.keep, video.currentTime)
      if (jump === Infinity) video.currentTime = project.keep[0]?.[0] ?? 0
      video.play()
    } else video.pause()
  }

  function cut() {
    if (editor.markIn === null || editor.markOut === null) return
    editor.cut(editor.markIn, editor.markOut)
    editor.markIn = editor.markOut = null
  }

  function matches(event: KeyboardEvent, combo: string) {
    const parts = combo.toLowerCase().split('+')
    const key = parts.pop()
    return (
      event.key.toLowerCase() === key &&
      parts.includes('ctrl') === (event.ctrlKey || event.metaKey) &&
      parts.includes('shift') === event.shiftKey
    )
  }

  function onKey(event: KeyboardEvent) {
    const target = event.target as HTMLElement
    if (target.closest('input, textarea, select')) return
    const actions: Record<string, () => void> = {
      play: togglePlay,
      mark_in: () => (editor.markIn = video.currentTime),
      mark_out: () => (editor.markOut = video.currentTime),
      cut,
      back: () => player.seek(video.currentTime - 1),
      forward: () => player.seek(video.currentTime + 1),
      undo: () => editor.undo(),
      redo: () => editor.redo(),
    }
    for (const [name, run] of Object.entries(actions)) {
      if (matches(event, (shortcuts as Record<string, string>)[name])) {
        event.preventDefault()
        run()
        return
      }
    }
  }
</script>

<svelte:window onkeydown={onKey} />

<section class="player">
  <div class="screen">
    <!-- svelte-ignore a11y_media_has_caption: the captions are drawn by JASSUB -->
    <video bind:this={video} src="/api/media" controls preload="auto"></video>
  </div>

  <div class="controls">
    <span class="time" bind:this={clockEl}>0:00.00</span>
    <button onclick={togglePlay}>⏯</button>
    <button onclick={() => (editor.markIn = video.currentTime)}>{t('player.mark_in')} (I)</button>
    <button onclick={() => (editor.markOut = video.currentTime)}>{t('player.mark_out')} (O)</button>
    <button class="danger" disabled={editor.markIn === null || editor.markOut === null} onclick={cut}>
      {t('player.cut', { start: clock(Math.min(editor.markIn ?? 0, editor.markOut ?? 0)), end: clock(Math.max(editor.markIn ?? 0, editor.markOut ?? 0)) })} (X)
    </button>
    <span class="muted">{t('player.output', { time: clock(outputDuration(project.keep)) })}</span>
  </div>
  <p class="muted">{t('player.hint')}</p>
</section>

<style>
  .screen { background: #000; border-radius: 8px; overflow: hidden; }
  video { display: block; width: 100%; max-height: 58vh; }
  .controls { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-top: 0.6rem; }
  .time { font-variant-numeric: tabular-nums; min-width: 5.5em; }
  .danger:not(:disabled) { background: var(--cut); }
</style>
