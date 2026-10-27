<script lang="ts">
  // The removed parts of the video; each one can be restored (its subtitles come back).
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { clock, cutsOf } from '../lib/timeline'

  const project = $derived(editor.project!)
  const cuts = $derived(cutsOf(project.keep, project.duration))
</script>

<section>
  <h2>{t('cuts.title')}</h2>
  {#if cuts.length === 0}
    <p class="muted">{t('cuts.empty')}</p>
  {/if}
  <ul>
    {#each cuts as cut (cut[0])}
      <li>
        <button class="link" onclick={() => player.seek(cut[0])}>{clock(cut[0])} – {clock(cut[1])}</button>
        <button onclick={() => editor.restore(cut)}>{t('cuts.restore')}</button>
      </li>
    {/each}
  </ul>
</section>

<style>
  ul { list-style: none; margin: 0; padding: 0; }
  li { display: flex; justify-content: space-between; gap: 0.5rem; padding: 0.25rem 0; }
  .link { background: none; padding: 0; font-variant-numeric: tabular-nums; color: var(--cut); }
</style>
