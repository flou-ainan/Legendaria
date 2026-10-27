<script lang="ts">
  // The page: pick a video, transcribe it, then edit. Everything happens under the video and on the
  // timeline; the side drawer (subtitle list, glossary, cuts, export) is optional.
  import { onMount } from 'svelte'
  import Browse from './components/Browse.svelte'
  import Drawer from './components/Drawer.svelte'
  import Inspector from './components/Inspector.svelte'
  import Menu from './components/Menu.svelte'
  import Player from './components/Player.svelte'
  import Timeline from './components/Timeline.svelte'
  import Transcribe from './components/Transcribe.svelte'
  import Welcome from './components/Welcome.svelte'
  import { loadState, openVideo, type State } from './lib/api'
  import { editor } from './lib/editor.svelte'
  import { t } from './lib/i18n'
  import { ui } from './lib/ui.svelte'

  let info = $state<State | null>(null)
  let failure = $state('')

  onMount(async () => {
    try {
      show(await loadState())
    } catch (error) {
      failure = (error as Error).message
    }
  })

  // `restored`: the project came from the copy in this browser, so it is saved to the server again.
  function show(next: State, restored = false) {
    info = next
    editor.fonts = next.fonts
    editor.base = next.base
    const video = next.video
      ? { path: next.path ?? '', name: next.video, duration: next.media.duration, width: next.media.width, height: next.media.height }
      : null
    editor.load(next.project, video, restored)
    if (restored) void editor.saveNow()
  }

  // Back to the start screen (the project stays saved next to the video).
  const closeVideo = () => info && show({ ...info, video: null, project: null })

  let generating = $state(false) // the Generate captions sheet over the editor
  let browsing = $state(false) // the file browser opened from the menu

  async function openFromMenu(path: string) {
    browsing = false
    try {
      await editor.saveNow()
      show(await openVideo(path))
    } catch (error) {
      failure = (error as Error).message
    }
  }

  // A copy of the project to keep elsewhere (the working copy is saved next to the video on its own).
  function download() {
    if (!editor.project || !info?.video) return
    const blob = new Blob([JSON.stringify($state.snapshot(editor.project), null, 2)], { type: 'application/json' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${info.video}.legendaria.json`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  const saveLabel = $derived(
    editor.saveStatus === 'saving' ? t('saving')
    : editor.saveStatus === 'error' ? t('save_error', { message: editor.saveError })
    : t('saved'),
  )
</script>

{#if failure}
  <p class="error center">{t('server_error', { message: failure })}</p>
{:else if !info}
  <p class="muted center">{t('loading')}</p>
{:else if !info.video}
  <Welcome onOpen={show} />
{:else if !editor.project}
  <Transcribe {info} onDone={(project) => editor.load(project)} onChange={closeVideo} />
{:else}
  <header>
    <Menu onOpenVideo={() => (browsing = true)} onOpenProject={() => (browsing = true)} onNew={closeVideo} onGenerate={() => (generating = true)} onSave={() => editor.saveNow()} onDownload={download} />
    <img class="logo" src="/logo.svg" alt="" />
    <strong class="brand">Legendária</strong>
    <button class="link" onclick={closeVideo} title={t('header.open')}>{info.video}</button>
    <span class="spacer"></span>
    <span class="muted" class:error={editor.saveStatus === 'error'}>{saveLabel}</span>
    {#each ['subtitles', 'glossary', 'cuts'] as const as panel (panel)}
      <button class="panel" class:on={ui.panel === panel} onclick={() => ui.toggle(panel)}>{t(`panel.${panel}`)}</button>
    {/each}
    <button class="primary export" onclick={() => ui.toggle('export')}>{t('panel.export')}</button>
  </header>
  <main class:drawer={ui.panel}>
    <div class="stage"><Player font={info.font} fonts={info.fonts} /></div>
    <Drawer />
    <div class="lower">
      <Timeline />
      <Inspector />
    </div>
  </main>
{/if}

{#if generating && info}
  <Transcribe {info} sheet onDone={(project) => { generating = false; editor.load(project) }} onChange={() => (generating = false)} />
{/if}

{#if browsing}
  <Browse onClose={() => (browsing = false)} onPick={openFromMenu} />
{/if}

<style>
  header { display: flex; gap: 0.5rem; align-items: center; padding: 0.5rem 1rem; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
  header .on { background: var(--accent); color: #15131c; }
  .link { background: none; color: var(--muted); padding: 0; text-decoration: underline dotted; overflow-wrap: anywhere; text-align: left; }
  .spacer { flex: 1; }
  .logo { width: 1.6rem; height: 1.6rem; }
  .brand { white-space: nowrap; }
  .export { order: 99; } /* always the last, at the top right */
  @media (max-width: 899px) {
    .panel, .brand { display: none; }
    .link { max-width: 40vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  }
  main { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.8rem; padding: 0.8rem; align-items: start; }
  main.drawer { grid-template-columns: minmax(0, 1fr) 25rem; }
  main.drawer :global(aside) { grid-column: 2; grid-row: 1 / span 2; max-height: calc(100vh - 6rem); position: sticky; top: 0.8rem; }
  .lower { display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; gap: 0.8rem; background: var(--panel); border-radius: 10px; padding: 0.8rem; }
  .center { text-align: center; margin-top: 30vh; }
  @media (max-width: 900px) {
    main.drawer { grid-template-columns: minmax(0, 1fr); }
    main { padding: 0.5rem; }
  }
</style>
