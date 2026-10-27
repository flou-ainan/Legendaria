<script lang="ts">
  // First screen when no video is open: drop a file here, or choose one from the computer.
  import { openVideo, uploadVideo, type State } from '../lib/api'
  import { t } from '../lib/i18n'
  import Browse from './Browse.svelte'

  let { onOpen }: { onOpen: (state: State) => void } = $props()

  let dragging = $state(false)
  let busy = $state(false)
  let progress = $state(0)
  let error = $state('')
  let browsing = $state(false)

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
    <h1>Legendária</h1>
    <p class="drop">{dragging ? t('welcome.release') : t('welcome.drop')}</p>
    <p class="muted">{t('welcome.or')}</p>
    <button class="primary big" onclick={() => (browsing = true)} disabled={busy}>{t('welcome.choose')}</button>
    {#if busy}<progress max="1" value={progress || undefined}></progress>{/if}
    {#if error}<p class="error">{error}</p>{/if}
    <p class="muted small">{t('welcome.note')}</p>
  </section>
</main>

{#if browsing}
  <Browse onClose={() => (browsing = false)} onPick={(path) => { browsing = false; run(openVideo(path)) }} />
{/if}

<style>
  main { min-height: 100vh; display: grid; place-items: center; padding: 1rem; border: 3px dashed transparent; }
  main.dragging { border-color: var(--accent); background: #ffd23f10; }
  .card { text-align: center; max-width: 28rem; display: grid; gap: 0.6rem; justify-items: center; }
  h1 { margin: 0; }
  .drop { font-size: 1.2rem; margin: 1rem 0 0; }
  .big { font-size: 1.05rem; padding: 0.7rem 1.4rem; }
  progress { width: 100%; }
  .small { font-size: 0.8rem; max-width: 24rem; }
</style>
