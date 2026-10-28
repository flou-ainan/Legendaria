<script lang="ts">
  // Optional side panel: subtitle list, glossary, cuts, export. Closed by default; the work
  // happens under the video and on the timeline (CapCut / InShot style).
  import { fly } from 'svelte/transition'
  import { t } from '../lib/i18n'
  import { ui, type Panel } from '../lib/ui.svelte'
  import CueList from './CueList.svelte'
  import Cuts from './Cuts.svelte'
  import Export from './Export.svelte'
  import Glossary from './Glossary.svelte'
  import Review from './Review.svelte'

  const tabs: Panel[] = ['subtitles', 'glossary', 'cuts', 'export']
</script>

{#if ui.panel}
  <aside transition:fly={{ y: 320, duration: matchMedia('(max-width: 1023px)').matches ? 220 : 0 }}>
    <nav>
      {#each tabs as tab (tab)}
        <button class:on={ui.panel === tab} onclick={() => (ui.panel = tab)}>{t(`panel.${tab}`)}</button>
      {/each}
      <span class="spacer"></span>
      <button onclick={() => (ui.panel = null)} title={t('panel.close')}>✕</button>
    </nav>
    <div class="body">
      {#if ui.panel === 'subtitles'}<CueList />
      {:else if ui.panel === 'glossary'}<Glossary /><Review />
      {:else if ui.panel === 'cuts'}<Cuts />
      {:else}<Export />{/if}
    </div>
  </aside>
{/if}

<style>
  aside { background: var(--panel); border-radius: 10px; display: flex; flex-direction: column; min-height: 0; }
  nav { display: flex; gap: 0.3rem; padding: 0.5rem; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
  nav .on { background: var(--accent); color: #15131c; }
  .spacer { flex: 1; }
  .body { padding: 0.8rem; overflow-y: auto; min-height: 0; }
  /* narrow screens: a bottom sheet over the editor */
  @media (max-width: 1023px) {
    aside { position: fixed; left: 0; right: 0; bottom: 0; max-height: 44vh; border-radius: 14px 14px 0 0; z-index: 20; box-shadow: 0 -8px 30px #000a; }
  }
</style>
