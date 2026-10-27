<script lang="ts">
  // The menu: File actions, panels and interface language. A hamburger on narrow screens, "File" on wide ones.
  import { interfaceLanguages, lang, setLang, t } from '../lib/i18n'
  import { ui, type Panel } from '../lib/ui.svelte'

  let {
    onOpenVideo, onOpenProject, onNew, onGenerate, onSave, onDownload,
  }: { onGenerate: () => void; onOpenVideo: () => void; onOpenProject: () => void; onNew: () => void; onSave: () => void; onDownload: () => void } = $props()

  let open = $state(false)
  const panels: Panel[] = ['subtitles', 'glossary', 'cuts', 'export']
  const run = (action: () => void) => () => {
    open = false
    action()
  }
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && (open = false)} />

<div class="menu">
  <button onclick={() => (open = !open)} aria-expanded={open} aria-label={t('menu.title')}>
    <span class="burger">☰</span><span class="word">{t('menu.file')} ▾</span>
  </button>
  {#if open}
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="shade" onclick={() => (open = false)}></div>
    <div class="list" role="menu">
      <button role="menuitem" onclick={run(onOpenVideo)}>{t('menu.open_video')}</button>
      <button role="menuitem" onclick={run(onOpenProject)}>{t('menu.open_project')}</button>
      <button role="menuitem" onclick={run(onNew)}>{t('menu.new')}</button>
      <hr />
      <button role="menuitem" onclick={run(onGenerate)}>{t('menu.generate')}</button>
      <button role="menuitem" onclick={run(onSave)}>{t('menu.save')}</button>
      <button role="menuitem" onclick={run(onDownload)}>{t('menu.download')}</button>
      <button role="menuitem" onclick={run(() => (ui.panel = 'export'))}>{t('menu.export')}</button>
      <hr class="narrow" />
      {#each panels as panel (panel)}
        <button role="menuitem" class="narrow" onclick={run(() => ui.toggle(panel))}>{t(`panel.${panel}`)}</button>
      {/each}
      <hr />
      <span class="label muted">{t('menu.language')}</span>
      {#each interfaceLanguages as [code, name] (code)}
        <button role="menuitemradio" aria-checked={code === lang} class:on={code === lang} onclick={() => setLang(code)}>{name}</button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .menu { position: relative; }
  .word { display: none; }
  .shade { position: fixed; inset: 0; z-index: 30; }
  .list {
    position: absolute; top: 110%; left: 0; z-index: 31; min-width: 17rem; display: grid; gap: 0.15rem;
    background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 0.35rem; box-shadow: 0 10px 30px #000a;
  }
  .list button { text-align: left; background: none; padding: 0.5rem 0.6rem; }
  .list button:hover { background: var(--line); }
  .list .on { color: var(--accent); }
  hr { border: 0; border-top: 1px solid var(--line); width: 100%; margin: 0.2rem 0; }
  .label { padding: 0.2rem 0.6rem; }
  @media (min-width: 900px) {
    .burger, .narrow { display: none; }
    .word { display: inline; }
  }
</style>
