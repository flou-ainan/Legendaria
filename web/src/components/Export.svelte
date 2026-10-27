<script lang="ts">
  // Export: the edited video with burned-in subtitles, or subtitle files (cut timing applied).
  import { runJob } from '../lib/api'
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'

  let busy = $state(false)
  let progress = $state(0)
  let message = $state('')

  async function exportAs(format: string) {
    busy = true
    progress = 0
    message = ''
    const last = await runJob('/api/export', { format }, (e) => {
      if (e.event === 'progress') progress = Math.round((100 * Number(e.t)) / Number(e.total || 1))
    })
    busy = false
    message =
      last.event === 'done'
        ? t('export.done', { path: String((last.outputs as string[])[0]) })
        : t('error', { message: String(last.message) })
  }
</script>

<section>
  <h2>{t('export.title')}</h2>
  <div class="buttons">
    <button class="primary" disabled={busy || editor.saveStatus !== 'saved'} onclick={() => exportAs('mp4')}>{t('export.mp4')}</button>
    {#each ['srt', 'vtt', 'ass'] as format (format)}
      <button disabled={busy || editor.saveStatus !== 'saved'} onclick={() => exportAs(format)}>{format.toUpperCase()}</button>
    {/each}
  </div>
  {#if busy}<progress max="100" value={progress}></progress> <span class="muted">{t('export.running', { pct: progress })}</span>{/if}
  {#if message}<p class="muted">{message}</p>{/if}
</section>

<style>
  .buttons { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.5rem; }
  progress { width: 100%; }
  p { word-break: break-all; }
</style>
