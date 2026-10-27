<script lang="ts">
  // First screen: transcribe the video into a new project.
  import { untrack } from 'svelte'
  import { runJob, type Project, type State } from '../lib/api'
  import { t } from '../lib/i18n'

  let { info, onDone }: { info: State; onDone: (project: Project) => void } = $props()

  let model = $state(untrack(() => info.model)) // initial value only
  let language = $state(untrack(() => info.language)) // initial value only
  let style = $state(untrack(() => info.style)) // initial value only
  let status = $state('')
  let error = $state('')
  let busy = $state(false)

  async function start() {
    busy = true
    error = ''
    const last = await runJob('/api/transcribe', { model, language, style }, (e) => {
      if (e.event === 'progress') {
        status = t('transcribe.running', { pct: Math.round((100 * Number(e.t)) / Number(e.total || 1)) })
      } else if (e.event === 'model_download') {
        const total = Number(e.total || 0)
        status = t('transcribe.download', {
          pct: total ? `${Math.round((100 * Number(e.downloaded)) / total)}%` : '',
        })
      }
    })
    busy = false
    if (last.event === 'done') onDone(last.project as Project)
    else error = t('error', { message: String(last.message) })
  }
</script>

<section class="card">
  <h1>{t('transcribe.title', { video: info.video })}</h1>
  <p class="muted">{t('transcribe.intro')}</p>
  <label>{t('transcribe.model')} <input bind:value={model} disabled={busy} /></label>
  <label>{t('transcribe.language')} <input bind:value={language} disabled={busy} /></label>
  <label>
    {t('transcribe.style')}
    <select bind:value={style} disabled={busy}>
      {#each info.styles as name (name)}<option>{name}</option>{/each}
    </select>
  </label>
  <button class="primary" onclick={start} disabled={busy}>{t('transcribe.start')}</button>
  {#if busy}<p>{status || t('loading')}</p>{/if}
  {#if error}<p class="error">{error}</p>{/if}
</section>

<style>
  .card { max-width: 32rem; margin: 10vh auto; padding: 1.5rem; background: var(--panel); border-radius: 12px; }
  h1 { font-size: 1.3rem; margin-top: 0; }
  label { display: grid; gap: 0.25rem; margin-bottom: 0.7rem; color: var(--muted); }
</style>
