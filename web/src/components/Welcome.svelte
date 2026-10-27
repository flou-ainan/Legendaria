<script lang="ts">
  // First screen when no video is open: drop a file here, or choose one from the computer.
  import { onMount } from 'svelte'
  import { openVideo, uploadVideo, type State } from '../lib/api'
  import { t } from '../lib/i18n'
  import { clock } from '../lib/timeline'
  import { forget, lastWork, sameVideo, type Snapshot } from '../lib/recovery'
  import Browse from './Browse.svelte'

  // `restored`: the project comes from the copy kept in this browser, so it must be saved again.
  let { onOpen }: { onOpen: (state: State, restored?: boolean) => void } = $props()

  let dragging = $state(false)
  let busy = $state(false)
  let progress = $state(0)
  let error = $state('')
  let browsing = $state(false)
  let last = $state<Snapshot | null>(null) // the work remembered by this browser
  let relinking = $state(false) // its video is gone: ask for it again
  let picking = $state<'new' | 'relink'>('new')

  onMount(async () => (last = await lastWork()))

  const ratio = (w: number | null, h: number | null) => (w && h ? (w / h).toFixed(2) : '?')

  /** Reopen the last video; the browser's copy of the project wins only if the server's save did not finish. */
  async function resume() {
    if (!last) return
    busy = true
    error = ''
    try {
      const state = await openVideo(last.video.path)
      onOpen(last.dirty || !state.project ? { ...state, project: last.project } : state, last.dirty || !state.project)
    } catch {
      relinking = true
    } finally {
      busy = false
    }
  }

  /** The user picked a replacement video: accept it only if it has the same length and screen shape. */
  async function relink(path: string) {
    if (!last) return
    busy = true
    error = ''
    try {
      const state = await openVideo(path)
      const verdict = sameVideo(last.video, state.media)
      if (verdict.ok) {
        onOpen({ ...state, project: { ...last.project, source: state.video ?? last.project.source } }, true)
      } else if (verdict.reason === 'duration') {
        error = t('relink.duration', { found: clock(state.media.duration), expected: clock(last.video.duration) })
      } else {
        error = t('relink.shape', {
          found: ratio(state.media.width, state.media.height),
          expected: ratio(last.video.width, last.video.height),
        })
      }
    } catch (e) {
      error = (e as Error).message
    } finally {
      busy = false
    }
  }

  async function discard() {
    await forget()
    last = null
    relinking = false
  }

  async function run(task: Promise<State>) {
    busy = true
    error = ''
    try {
      onOpen(await task)
    } catch (e) {
      error = (e as Error).message
    } finally {
      busy = false
    }
  }

  function onDrop(event: DragEvent) {
    event.preventDefault()
    dragging = false
    const file = event.dataTransfer?.files[0]
    if (file) run(uploadVideo(file, (fraction) => (progress = fraction)))
  }
</script>

<main
  class:dragging
  ondragover={(e) => { e.preventDefault(); dragging = true }}
  ondragleave={() => (dragging = false)}
  ondrop={onDrop}
>
  <section class="card">
    <img class="logo" src="/logo.svg" alt="" />
    <h1>Legendária</h1>
    {#if last && relinking}
      <div class="resume">
        <strong>{t('relink.title')}</strong>
        <p class="muted">{t('relink.body', { name: last.video.name, path: last.video.path })}</p>
        <button class="primary" onclick={() => { picking = 'relink'; browsing = true }} disabled={busy}>{t('relink.choose')}</button>
        <button class="link" onclick={discard}>{t('relink.forget')}</button>
      </div>
    {:else if last}
      <div class="resume">
        <strong>{t('recover.title')}</strong>
        <button class="primary" onclick={resume} disabled={busy}>{t('recover.resume', { name: last.video.name })}</button>
        <span class="muted">{t('recover.when', { when: new Date(last.savedAt).toLocaleString() })}</span>
        {#if last.dirty}<span class="muted">{t('recover.unsaved')}</span>{/if}
      </div>
    {/if}
    <p class="drop">{dragging ? t('welcome.release') : t('welcome.drop')}</p>
    <p class="muted">{t('welcome.or')}</p>
    <button class="primary big" onclick={() => { picking = 'new'; browsing = true }} disabled={busy}>{t('welcome.choose')}</button>
    {#if busy}<progress max="1" value={progress || undefined}></progress>{/if}
    {#if error}<p class="error">{error}</p>{/if}
    <p class="muted small">{t('welcome.note')}</p>
  </section>
</main>

{#if browsing}
  <Browse onClose={() => (browsing = false)} onPick={(path) => { browsing = false; if (picking === 'relink') relink(path); else run(openVideo(path)) }} />
{/if}

<style>
  main { min-height: 100vh; display: grid; place-items: center; padding: 1rem; border: 3px dashed transparent; }
  main.dragging { border-color: var(--accent); background: #ffd23f10; }
  .card { text-align: center; max-width: 28rem; display: grid; gap: 0.6rem; justify-items: center; }
  h1 { margin: 0; }
  .logo { width: 5rem; height: 5rem; }
  .resume { display: grid; gap: 0.4rem; justify-items: center; background: var(--panel); border-radius: 10px; padding: 0.8rem 1rem; }
  .link { background: none; color: var(--muted); text-decoration: underline dotted; }
  .drop { font-size: 1.2rem; margin: 1rem 0 0; }
  .big { font-size: 1.05rem; padding: 0.7rem 1.4rem; }
  progress { width: 100%; }
  .small { font-size: 0.8rem; max-width: 24rem; }
</style>
