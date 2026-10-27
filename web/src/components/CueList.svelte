<script lang="ts">
  // The subtitle list: edit text and times, split, merge, delete, add.
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { skipTarget } from '../lib/timeline'

  const project = $derived(editor.project!)
  let list: HTMLOListElement

  // $effect re-runs when what it reads changes: keep the current cue in view.
  $effect(() => {
    const row = list?.children[editor.current] as HTMLElement | undefined
    row?.scrollIntoView({ block: 'nearest' })
  })

  const inCut = (start: number, end: number) => skipTarget(project.keep, (start + end) / 2) !== null
  const seconds = (value: string) => Number.parseFloat(value.replace(',', '.'))
</script>

<section>
  <header>
    <h2>{t('cues.title')} ({project.cues.length})</h2>
    <button onclick={() => editor.addAt(player.time())}>+ {t('cues.add')}</button>
  </header>
  <ol bind:this={list}>
    {#each project.cues as cue, i (i)}
      <li class:current={i === editor.current} class:cut={inCut(cue.start, cue.end)}>
        <div class="times">
          <button class="seek" onclick={() => player.seek(cue.start)} title="▶">▶</button>
          <input
            type="number" step="0.01" min="0" value={cue.start.toFixed(2)}
            onchange={(e) => editor.setTimes(i, seconds(e.currentTarget.value), cue.end)}
          />
          <input
            type="number" step="0.01" min="0" value={cue.end.toFixed(2)}
            onchange={(e) => editor.setTimes(i, cue.start, seconds(e.currentTarget.value))}
          />
        </div>
        <textarea rows="1" value={cue.text} oninput={(e) => editor.setText(i, e.currentTarget.value)}></textarea>
        <div class="actions">
          <button onclick={() => editor.split(i, player.time())} title={t('cues.split')}>✂</button>
          <button onclick={() => editor.mergeNext(i)} disabled={i === project.cues.length - 1} title={t('cues.merge')}>⤓</button>
          <button onclick={() => editor.remove(i)} title={t('cues.delete')}>🗑</button>
        </div>
        {#if inCut(cue.start, cue.end)}<span class="muted note">{t('cues.in_cut')}</span>{/if}
      </li>
    {/each}
  </ol>
</section>

<style>
  header { display: flex; justify-content: space-between; align-items: center; }
  ol { list-style: none; margin: 0; padding: 0; max-height: 70vh; overflow-y: auto; }
  li {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 0.4rem;
    align-items: center;
    padding: 0.35rem;
    border-left: 3px solid transparent;
    border-bottom: 1px solid var(--line);
  }
  li.current { border-left-color: var(--accent); background: #ffd23f12; }
  li.cut { opacity: 0.5; }
  .times { display: flex; gap: 0.25rem; }
  .times input { width: 5.2em; }
  .seek { padding: 0.3rem 0.45rem; }
  textarea { width: 100%; resize: vertical; }
  .actions { display: flex; gap: 0.2rem; }
  .actions button { padding: 0.3rem 0.45rem; }
  .note { grid-column: 1 / -1; }
</style>
