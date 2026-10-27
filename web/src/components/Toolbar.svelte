<script lang="ts">
  // The tool row under the video (CapCut / Kdenlive style): undo/redo first, then play, mark, cut, split, snap magnet.
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { clock, outputDuration } from '../lib/timeline'
  import { ui } from '../lib/ui.svelte'
  import { fly } from 'svelte/transition'
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
  <div class="pop" transition:fly={{ y: 320, duration: matchMedia('(max-width: 1023px)').matches ? 220 : 0 }}>
    <button class="grab" onclick={() => (lookOpen = false)} aria-label={t('panel.close')}></button>
    <LookMenu />
  </div>
{/if}

<style>
  .pop { margin-top: 0.4rem; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 0.8rem; width: fit-content; max-width: 100%; }
  .grab { display: none; }
  .toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; margin-top: 0.5rem; }
  .tool { display: inline-grid; place-items: center; width: 2.4rem; height: 2.4rem; min-width: 0; min-height: 0; padding: 0; }
  .tool.on { background: var(--accent); color: #15131c; }
  .cut:not(:disabled), .danger:hover:not(:disabled) { background: var(--cut); }
  .time { font-variant-numeric: tabular-nums; min-width: 5.2em; padding: 0 0.4rem; }
  .sep { width: 1px; align-self: stretch; background: var(--line); margin: 0 0.2rem; }
  .spacer { flex: 1; }
  .length { font-size: 0.8rem; }
  /* narrow screens: a single row that slides sideways, like mobile editors */
  @media (max-width: 1023px) {
    /* the look menu is a bottom sheet on narrow screens */
    .pop { position: fixed; left: 0; right: 0; bottom: 0; width: auto; z-index: 30; margin: 0; border-radius: 14px 14px 0 0; box-shadow: 0 -8px 30px #000a; padding-top: 0.4rem; }
    .grab { display: block; width: 3rem; height: 0.35rem; padding: 0; margin: 0 auto 0.6rem; border-radius: 1rem; background: var(--line); }
    .toolbar { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; gap: 0.15rem; padding-bottom: 0.2rem; }
    .toolbar::-webkit-scrollbar { display: none; }
    .toolbar > * { flex: none; }
    .tool { width: 2.1rem; height: 2.1rem; }
    .tool :global(svg) { width: 1.15rem; height: 1.15rem; }
    .length, .spacer { display: none; }
  }
</style>
