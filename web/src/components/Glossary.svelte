<script lang="ts">
  // The glossary library: pick the active one, add a word or a correction, import and export.
  import { onMount } from 'svelte'
  import { addGlossaryEntry, importGlossary, loadGlossary, useGlossary, type GlossaryState } from '../lib/api'
  import { t } from '../lib/i18n'

  let glossary = $state<GlossaryState | null>(null)
  let entry = $state('')
  let newName = $state('')
  let message = $state('')
  let file = $state<HTMLInputElement>()

  const refresh = async () => (glossary = await loadGlossary())
  onMount(refresh)

  const entries = $derived(glossary ? glossary.text.split('\n').filter((l) => l.trim() && !l.startsWith('#')).length : 0)

  async function attempt(task: () => Promise<void>) {
    try {
      await task()
    } catch (e) {
      message = t('error', { message: (e as Error).message })
    }
  }

  const add = () =>
    attempt(async () => {
      if (!entry.trim()) return
      const { added } = await addGlossaryEntry(entry)
      message = added ? t('glossary.added', { entry: entry.trim() }) : t('glossary.exists')
      entry = ''
      await refresh()
    })

  const choose = (name: string) =>
    attempt(async () => {
      glossary = await useGlossary(name)
    })

  const create = () =>
    attempt(async () => {
      if (!newName.trim()) return
      glossary = await useGlossary(newName.trim())
      newName = ''
    })

  const upload = () =>
    attempt(async () => {
      const picked = file?.files?.[0]
      if (!picked) return
      glossary = await importGlossary(picked.name.replace(/\.[^.]+$/, ''), await picked.text())
      message = t('glossary.imported', { name: glossary.active })
      if (file) file.value = ''
    })
</script>

<section>
  <h2>{t('glossary.title')}</h2>
  {#if glossary}
    <label class="row">
      <span class="muted">{t('glossary.active')}</span>
      <select value={glossary.active} onchange={(e) => choose(e.currentTarget.value)}>
        {#each glossary.names as name (name)}<option>{name}</option>{/each}
      </select>
    </label>
    <p class="muted small">{t('glossary.entries', { n: entries })}</p>
    <form onsubmit={(e) => { e.preventDefault(); add() }}>
      <input bind:value={entry} placeholder={t('glossary.add_hint')} aria-label={t('glossary.add')} />
      <button class="primary" type="submit">{t('glossary.add_btn')}</button>
    </form>
    <div class="row buttons">
      <button onclick={() => file?.click()}>{t('glossary.import')}</button>
      <input bind:this={file} type="file" accept=".txt,text/plain" hidden onchange={upload} />
      <a class="button" href={`/api/glossary/export?name=${encodeURIComponent(glossary.active)}`} download>{t('glossary.export')}</a>
    </div>
    <form onsubmit={(e) => { e.preventDefault(); create() }}>
      <input bind:value={newName} placeholder={t('glossary.new_hint')} aria-label={t('glossary.new')} />
      <button type="submit">{t('glossary.new')}</button>
    </form>
  {/if}
  {#if message}<p class="muted">{message}</p>{/if}
</section>

<style>
  .row { display: flex; gap: 0.5rem; align-items: center; }
  .row select { flex: 1; }
  form { display: flex; gap: 0.4rem; margin: 0.6rem 0; }
  form input { flex: 1; min-width: 0; }
  .buttons { margin: 0.6rem 0; }
  .small { margin: 0.3rem 0; }
  a.button { color: var(--text); background: var(--line); border-radius: 6px; padding: 0.35rem 0.7rem; text-decoration: none; }
</style>
