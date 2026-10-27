<script lang="ts">
  // Generate captions: pick model, language and style, then transcribe. A full page before the first run,
  // a sheet over the editor afterwards (`sheet`), where it keeps the cuts and the look and replaces the cues.
  import { untrack } from 'svelte'
  import { runJob, type Project, type State } from '../lib/api'
  import { t } from '../lib/i18n'

  let { info, onDone, onChange, sheet = false }: { info: State; onDone: (project: Project) => void; onChange: () => void; sheet?: boolean } = $props()

  let model = $state(untrack(() => info.model)) // initial values only; the user picks from here
  let language = $state(untrack(() => info.language))
  let style = $state(untrack(() => info.style))
  let status = $state('')
  let error = $state('')
  let busy = $state(false)

  const label = (m: State['models'][number]) =>
    `${m.name} · ${m.size_mb ? `${m.size_mb} MB · ` : ''}${m.installed ? t('model.installed') : t('model.download')}`
  const note = $derived(info.models.find((m) => m.name === model)?.notes ?? '')

  async function start() {
    busy = true
    error = ''
    const last = await runJob('/api/transcribe', { model, language, style }, (e) => {
      if (e.event === 'progress') {
        status = t('transcribe.running', { pct: Math.round((100 * Number(e.t)) / Number(e.total || 1)) })
      } else if (e.event === 'model_download') {
        const total = Number(e.total || 0)
        status = t('transcribe.download', { pct: total ? `${Math.round((100 * Number(e.downloaded)) / total)}%` : '' })
      }
    })
    busy = false
    if (last.event === 'done') onDone(last.project as Project)
    else error = t('error', { message: String(last.message) })
  }
</script>

<div class:shade={sheet}>
<section class="card" class:sheet>
  <h1>{sheet ? t('transcribe.sheet_title') : t('transcribe.title', { video: info.video ?? '' })}</h1>
  {#if !sheet}<p class="muted">{t('transcribe.intro')}</p>{/if}
  <label>
    {t('transcribe.model')}
    <select bind:value={model} disabled={busy}>
      {#each info.models as m (m.name)}<option value={m.name}>{label(m)}</option>{/each}
    </select>
    <span class="muted small">{note}</span>
  </label>
  <label>
    {t('transcribe.language')}
    <select bind:value={language} disabled={busy}>
      {#each info.languages as l (l.code)}<option value={l.code}>{l.name} ({l.code})</option>{/each}
    </select>
  </label>
  <label>
    {t('transcribe.style')}
    <select bind:value={style} disabled={busy}>
      {#each info.styles as name (name)}<option>{name}</option>{/each}
    </select>
  </label>
  <div class="row">
    <button class="primary" onclick={start} disabled={busy}>{t('transcribe.start')}</button>
    <button onclick={onChange} disabled={busy}>{sheet ? t('cancel') : t('header.open')}</button>
  </div>
  {#if busy}<p>{status || t('loading')}</p>{/if}
  {#if error}<p class="error">{error}</p>{/if}
  {#if sheet}<p class="muted small">{t('transcribe.replaces')}</p>{/if}
</section>
</div>

<style>
  .card { max-width: 32rem; margin: 10vh auto; padding: 1.5rem; background: var(--panel); border-radius: 12px; }
  h1 { font-size: 1.3rem; margin-top: 0; overflow-wrap: anywhere; }
  label { display: grid; gap: 0.25rem; margin-bottom: 0.8rem; color: var(--muted); }
  select { padding: 0.5rem; }
  .shade { position: fixed; inset: 0; background: #000a; z-index: 60; display: grid; place-items: center; }
  .sheet { margin: 0; width: min(32rem, 94vw); max-height: 92vh; overflow-y: auto; }
  .small { font-size: 0.8rem; }
  .row { display: flex; gap: 0.5rem; }
</style>
