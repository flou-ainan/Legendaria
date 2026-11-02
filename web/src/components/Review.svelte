<script lang="ts">
  // Glossary corrections for the current subtitles (the engine's layer 2, no AI). Apply one or all.
  import { loadReview, type Suggestion } from '../lib/api'
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'

  let items = $state<Suggestion[]>([])
  let checked = $state(false)
  let failure = $state('')

  async function run() {
    failure = ''
    try {
      items = await loadReview()
      checked = true
    } catch (error) {
      failure = (error as Error).message
    }
  }

  function apply(chosen: Suggestion[]) {
    editor.applySuggestions(chosen)
    items = items.filter((item) => !chosen.includes(item))
  }
</script>

<section>
  <header>
    <h2>{t('review.title')}</h2>
    <button onclick={run}>{t('review.run')}</button>
    {#if items.length > 1}<button class="primary" onclick={() => apply(items)}>{t('review.apply_all', { n: items.length })}</button>{/if}
  </header>
  {#if failure}<p class="error">{failure}</p>{/if}
  {#if checked && items.length === 0}<p class="muted">{t('review.none')}</p>{/if}
  <ul>
    {#each items as item (item.id)}
      <li>
        <button class="link" onclick={() => player.seek(item.start)}><s>{item.before}</s> → <strong>{item.after}</strong></button>
        <span class="muted">{item.reason}</span>
        <span class="actions">
          <button onclick={() => apply([item])}>{t('review.apply')}</button>
          <button onclick={() => (items = items.filter((i) => i !== item))}>{t('review.ignore')}</button>
        </span>
      </li>
    {/each}
  </ul>
</section>

<style>
  header { display: flex; gap: 0.5rem; align-items: baseline; }
  header h2 { flex: 1; }
  ul { list-style: none; margin: 0; padding: 0; }
  li { display: grid; gap: 0.2rem; padding: 0.4rem 0; border-bottom: 1px solid var(--line); }
  .link { background: none; padding: 0; text-align: left; }
  .actions { display: flex; gap: 0.3rem; }
</style>
