<script lang="ts">
  // The tool row under the video (CapCut / Kdenlive style): play, mark, cut, split, snap magnet, undo.
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'
  import { player } from '../lib/player'
  import { clock, outputDuration } from '../lib/timeline'
  import { ui } from '../lib/ui.svelte'

  let { clockEl = $bindable() }: { clockEl?: HTMLSpanElement } = $props()

  const project = $derived(editor.project!)
  const canCut = $derived(editor.markIn !== null && editor.markOut !== null)
</script>

<div class="toolbar" role="toolbar">
  <button class="tool" onclick={() => player.togglePlay()} title={t('tool.play')}><span>⏯</span><small>{t('tool.play_short')}</small></button>
  <span class="time" bind:this={clockEl}>0:00.00</span>
  <span class="sep"></span>
  <button class="tool" onclick={() => (editor.markIn = player.time())} title={t('tool.in')}><span>⟦</span><small>{t('tool.in_short')}</small></button>
  <button class="tool" onclick={() => (editor.markOut = player.time())} title={t('tool.out')}><span>⟧</span><small>{t('tool.out_short')}</small></button>
  <button class="tool cut" disabled={!canCut} onclick={() => player.cut()} title={t('tool.cut')}><span>✂</span><small>{t('tool.cut_short')}</small></button>
  <button class="tool" disabled={editor.current < 0} onclick={() => player.splitAtPlayhead()} title={t('tool.split')}><span>⫽</span><small>{t('tool.split_short')}</small></button>
  <button class="tool" class:on={ui.snap} aria-pressed={ui.snap} onclick={() => (ui.snap = !ui.snap)} title={ui.snap ? t('tool.snap_on') : t('tool.snap_off')}>
    <span class="magnet">🧲</span><small>{t('tool.snap_short')}</small>
  </button>
  <span class="sep"></span>
  <button class="tool" disabled={!editor.canUndo} onclick={() => editor.undo()} title={t('undo')}><span>↶</span><small>{t('undo')}</small></button>
  <button class="tool" disabled={!editor.canRedo} onclick={() => editor.redo()} title={t('redo')}><span>↷</span><small>{t('redo')}</small></button>
  <span class="spacer"></span>
  <span class="muted length">{t('player.output', { time: clock(outputDuration(project.keep)) })}</span>
</div>

<style>
  .toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; margin-top: 0.5rem; }
  .tool { display: grid; justify-items: center; gap: 0; min-width: 3.2rem; min-height: 2.8rem; padding: 0.2rem 0.5rem; }
  .tool span { font-size: 1.15rem; line-height: 1.3; }
  .tool small { font-size: 0.65rem; color: var(--muted); }
  .tool.on { background: var(--accent); }
  .tool.on small { color: #15131c; }
  .tool.on .magnet { filter: none; }
  .cut:not(:disabled) { background: var(--cut); }
  .time { font-variant-numeric: tabular-nums; min-width: 5.2em; padding: 0 0.4rem; }
  .sep { width: 1px; align-self: stretch; background: var(--line); margin: 0 0.2rem; }
  .spacer { flex: 1; }
  .length { font-size: 0.8rem; }
</style>
