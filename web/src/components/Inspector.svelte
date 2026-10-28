<script lang="ts">
  // Edit the selected block (click it on the timeline; double-click jumps to the text box).
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'

  const project = $derived(editor.project!)
  const index = $derived(editor.selected)
  const cue = $derived(project.cues[index])
  let box = $state<HTMLTextAreaElement>()

  // Runs when the counter is bumped (double-click on a block): focus the text.
  $effect(() => {
    if (editor.focusText && box) {
      box.focus()
      box.select()
    }
  })

  const seconds = (value: string) => Number.parseFloat(value.replace(',', '.'))
</script>

<section class="inspector">
  {#if cue}
    <textarea bind:this={box} rows="2" value={cue.text} oninput={(e) => editor.setText(index, e.currentTarget.value)} onkeydown={(e) => e.key === 'Escape' && e.currentTarget.blur()} aria-label={t('inspector.text')}></textarea>
    <div class="fields">
      <label>{t('inspector.start')}
        <input type="number" step="0.01" min="0" value={cue.start.toFixed(2)} onchange={(e) => editor.setTimes(index, seconds(e.currentTarget.value), cue.end)} />
      </label>
      <label>{t('inspector.end')}
        <input type="number" step="0.01" min="0" value={cue.end.toFixed(2)} onchange={(e) => editor.setTimes(index, cue.start, seconds(e.currentTarget.value))} />
      </label>
    </div>
  {/if}
</section>

<style>
  .inspector { display: grid; gap: 0.5rem; }
  .inspector:empty { display: none; }
  textarea { width: 100%; resize: vertical; font-size: 1rem; }
  .fields { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: end; }
  label { display: grid; gap: 0.15rem; font-size: 0.75rem; color: var(--muted); }
  input { width: 5.5em; }
</style>
