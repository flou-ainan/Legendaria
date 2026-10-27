<script lang="ts">
  // The tool row under the video (CapCut / Kdenlive style): undo/redo first, then play, mark, cut, split, snap magnet.
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { clock, outputDuration } from '../lib/timeline'
  import { ui } from '../lib/ui.svelte'
  import Icon from './Icon.svelte'
  import LookMenu from './LookMenu.svelte'

  let { clockEl = $bindable() }: { clockEl?: HTMLSpanElement } = $props()

  const project = $derived(editor.project!)
  let lookOpen = $state(false)
  const selected = $derived(editor.selected >= 0 && editor.selected < project.cues.length)
  const canCut = $derived(editor.markIn !== null && editor.markOut !== null)
</script>

<div class="toolbar" role="toolbar">
  <button class="tool" disabled={!editor.canUndo} onclick={() => editor.undo()} title={t('undo')}><Icon name="undo" /></button>
  <button class="tool" disabled={!editor.canRedo} onclick={() => editor.redo()} title={t('redo')}><Icon name="redo" /></button>
  <span class="sep"></span>
  <button class="tool" onclick={() => player.togglePlay()} title={t('tool.play')}><Icon name="play" /></button>
  <span class="time" bind:this={clockEl}>0:00.00</span>
  <span class="sep"></span>
  <!-- contextual: at most 5 tools, they change with the selection (plan 08) -->
  {#if selected}
    <button class="tool" onclick={() => editor.split(editor.selected, player.time())} title={t('tool.split')}><Icon name="split" /></button>
    <button class="tool" disabled={editor.selected >= project.cues.length - 1} onclick={() => editor.mergeNext(editor.selected)} title={t('cues.merge')}><Icon name="merge" /></button>
    <button class="tool danger" onclick={() => { editor.remove(editor.selected); editor.selected = -1 }} title={t('cues.delete')}><Icon name="remove" /></button>
  {:else}
    <button class="tool" onclick={() => (editor.markIn = player.time())} title={t('tool.in')}><Icon name="markIn" /></button>
    <button class="tool" onclick={() => (editor.markOut = player.time())} title={t('tool.out')}><Icon name="markOut" /></button>
    <button class="tool cut" disabled={!canCut} onclick={() => player.cut()} title={t('tool.cut')}><Icon name="cut" /></button>
  {/if}
  <button class="tool" class:on={lookOpen} aria-expanded={lookOpen} onclick={() => (lookOpen = !lookOpen)} title={t('look.title')}><Icon name="look" /></button>
  <span class="sep"></span>
  <button class="tool" class:on={ui.snap} aria-pressed={ui.snap} onclick={() => (ui.snap = !ui.snap)} title={ui.snap ? t('tool.snap_on') : t('tool.snap_off')}>
    <Icon name="snap" />
  </button>
  <span class="spacer"></span>
  <span class="muted length">{t('player.output', { time: clock(outputDuration(project.keep)) })}</span>
</div>
{#if lookOpen}
  <div class="pop"><LookMenu /></div>
{/if}

<style>
  .pop { margin-top: 0.4rem; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 0.8rem; width: fit-content; max-width: 100%; }
  .toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; margin-top: 0.5rem; }
  .tool { display: grid; justify-items: center; gap: 0; min-width: 2.6rem; min-height: 2.4rem; padding: 0.2rem 0.5rem; }
  .tool.on { background: var(--accent); color: #15131c; }
  .cut:not(:disabled), .danger:hover:not(:disabled) { background: var(--cut); }
  .time { font-variant-numeric: tabular-nums; min-width: 5.2em; padding: 0 0.4rem; }
  .sep { width: 1px; align-self: stretch; background: var(--line); margin: 0 0.2rem; }
  .spacer { flex: 1; }
  .length { font-size: 0.8rem; }
  /* narrow screens: a single row that slides sideways, like mobile editors */
  @media (max-width: 899px) {
    .toolbar { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; gap: 0.15rem; padding-bottom: 0.2rem; }
    .toolbar::-webkit-scrollbar { display: none; }
    .toolbar > * { flex: none; }
    .tool { min-width: 2.3rem; min-height: 2.2rem; padding: 0.15rem 0.35rem; }
    .tool :global(svg) { width: 1.15rem; height: 1.15rem; }
    .length, .spacer { display: none; }
  }
</style>
