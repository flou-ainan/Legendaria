<script lang="ts">
  // The video with the exact subtitle preview (JASSUB = libass in WebAssembly, the same
  // renderer FFmpeg uses on export), cut skipping and the in/out marks.
  import JASSUB from 'jassub'
  import { onDestroy, onMount } from 'svelte'
  import { previewAss, type FontEntry } from '../lib/api'
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { ui } from '../lib/ui.svelte'
  import Icon from './Icon.svelte'
  import Toolbar from './Toolbar.svelte'
  import shortcuts from '../lib/shortcuts.json'
  import { clock, skipTarget } from '../lib/timeline'

  let video: HTMLVideoElement
  let screen: HTMLDivElement
  let full = $state(false)
  let clockEl = $state<HTMLSpanElement>()
  let subs: JASSUB | undefined
  let frame = 0

  let { font, fonts }: { font: string; fonts: FontEntry[] } = $props()

  const project = $derived(editor.project!)
  // where the selected subtitle (or the track) sits: above the middle of the picture or below it
  const subtitlesHigh = $derived((project.cues[editor.selected]?.look?.y ?? project.look?.y ?? editor.base.y) > 0.5)
  $effect(() => {
    void ui.sheet, void subtitlesHigh // the box changes size: lay the subtitle canvas out again
    refit()
  })

  onMount(async () => {
    player.video = video
    // libass finds fonts by lowercase family name; without the file it uses JASSUB's bundled font.
    // The bundled families are all loaded up front, so changing the font in the Look menu is instant.
    const available: Record<string, string> = Object.fromEntries(fonts.map((f) => [f.family.toLowerCase(), `/api/fonts/${f.file}`]))
    const family = font.toLowerCase()
    if (!(family in available) && (await fetch('/api/font', { method: 'HEAD' })).ok) available[family] = '/api/font'
    subs = new JASSUB({
      video,
      subContent: await previewAss(),
      // `fonts` loads it up front, so the very first frame is drawn with it.
      ...(family in available ? { fonts: Object.values(available), availableFonts: available, defaultFont: family } : { fonts: Object.values(available), availableFonts: available }),
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
    if (clockEl) clockEl.textContent = clock(time)
    const index = project.cues.findIndex((c) => c.start <= time && time < c.end)
    if (index !== editor.current) editor.current = index
    frame = video.requestVideoFrameCallback(tick)
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

  // Full screen shows the box that holds the video AND the subtitle canvas; the <video>'s own full screen
  // would leave JASSUB's canvas behind (the subtitles disappeared). iPhones only allow the video itself.
  function toggleFullscreen() {
    if (document.fullscreenElement) void document.exitFullscreen()
    else if (screen.requestFullscreen) void screen.requestFullscreen()
    else (video as HTMLVideoElement & { webkitEnterFullscreen?: () => void }).webkitEnterFullscreen?.()
  }

  // The subtitle canvas is laid out from the video's size: redo it once the browser has settled after a
  // full-screen switch or a rotation (it can report the old size for a few frames).
  function refit() {
    for (const wait of [0, 150, 500]) {
      setTimeout(async () => {
        if (!subs) return
        await subs.ready
        void subs.resize()
      }, wait)
    }
  }

  function onKey(event: KeyboardEvent) {
    const target = event.target as HTMLElement
    if (target.closest('input, textarea, select')) return
    const actions: Record<string, () => void> = {
      play: () => player.togglePlay(),
      mark_in: () => (editor.markIn = video.currentTime),
      mark_out: () => (editor.markOut = video.currentTime),
      cut: () => player.cut(),
      split: () => player.splitAtPlayhead(),
      snap: () => (ui.snap = !ui.snap),
      deselect: () => (editor.selected = -1),
      back: () => player.seek(video.currentTime - 1),
      forward: () => player.seek(video.currentTime + 1),
      undo: () => editor.undo(),
      redo: () => editor.redo(),
      fullscreen: toggleFullscreen,
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

<svelte:window onkeydown={onKey} onresize={refit} onorientationchange={refit} />
<svelte:document onfullscreenchange={() => { full = document.fullscreenElement === screen; refit() }} />

<section class="player">
  <div class="screen" class:full bind:this={screen}>
    <!-- With a bottom sheet open on a narrow screen the viewport is short: a tall video is cropped there, keeping
         the part where the subtitles are (the bottom, or the top when they sit high). JASSUB's canvas lives in .frame. -->
    <div class="viewport" class:crop={ui.sheet} class:high={subtitlesHigh}>
      <div class="frame">
        <!-- svelte-ignore a11y_media_has_caption: the captions are drawn by JASSUB -->
        <video bind:this={video} src="/api/media" controls controlslist="nofullscreen" preload="auto" ondblclick={toggleFullscreen}></video>
      </div>
    </div>
    <button class="fs" onclick={toggleFullscreen} title={t('tool.fullscreen')} aria-label={t('tool.fullscreen')}>
      <Icon name={full ? 'exitFullscreen' : 'fullscreen'} />
    </button>
  </div>

  <Toolbar bind:clockEl />
</section>

<style>
  .screen { position: relative; background: #000; border-radius: 8px; overflow: hidden; }
  video { display: block; width: 100%; max-height: 44vh; }
  .frame { position: relative; }
  @media (max-width: 1023px) {
    .viewport.crop { display: flex; flex-direction: column; justify-content: flex-end; max-height: 34vh; overflow: hidden; }
    .viewport.crop.high { justify-content: flex-start; }
    .viewport.crop .frame { flex: none; }
    .viewport.crop video { max-height: none; height: auto; }
  }
  /* full screen: sized by the full-screen box itself (not vw/vh, which are stale for a moment after a phone is rotated) */
  .screen.full { border-radius: 0; position: fixed; inset: 0; width: 100%; height: 100%; }
  .screen.full .viewport, .screen.full .frame { position: absolute; inset: 0; max-height: none; }
  .screen.full video { position: absolute; inset: 0; width: 100%; height: 100%; max-height: none; object-fit: contain; }
  .fs { position: absolute; top: 0.5rem; right: 0.5rem; z-index: 5; display: grid; place-items: center; width: 2.2rem; height: 2.2rem; padding: 0; background: #000a; color: #fff; opacity: 0.7; }
  .fs:hover { opacity: 1; }
</style>
