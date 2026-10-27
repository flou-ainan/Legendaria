<script lang="ts">
  // The editor page: transcribe first, then player + cuts + export on the left, subtitles on the right.
  import { onMount } from 'svelte'
  import CueList from './components/CueList.svelte'
  import Cuts from './components/Cuts.svelte'
  import Export from './components/Export.svelte'
  import Player from './components/Player.svelte'
  import Transcribe from './components/Transcribe.svelte'
  import { loadState, type State } from './lib/api'
  import { editor } from './lib/editor.svelte'
  import { t } from './lib/i18n'

  let info = $state<State | null>(null)
  let failure = $state('')

  onMount(async () => {
    try {
      info = await loadState()
      if (info.project) editor.load(info.project)
    } catch (error) {
      failure = (error as Error).message
    }
  })

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
{:else if !editor.project}
  <Transcribe {info} onDone={(project) => editor.load(project)} />
{:else}
  <header>
    <strong>Legendária</strong>
    <span class="muted">{info.video}</span>
    <span class="spacer"></span>
    <span class="muted" class:error={editor.saveStatus === 'error'}>{saveLabel}</span>
    <button onclick={() => editor.undo()} disabled={!editor.canUndo}>↶ {t('undo')}</button>
    <button onclick={() => editor.redo()} disabled={!editor.canRedo}>↷ {t('redo')}</button>
  </header>
  <main>
    <div class="left">
      <Player font={info.font} />
      <div class="row">
        <Cuts />
        <Export />
      </div>
    </div>
    <div class="right"><CueList /></div>
  </main>
{/if}

<style>
  header { display: flex; gap: 0.75rem; align-items: center; padding: 0.6rem 1rem; border-bottom: 1px solid var(--line); }
  .spacer { flex: 1; }
  main { display: grid; grid-template-columns: minmax(0, 3fr) minmax(20rem, 2fr); gap: 1rem; padding: 1rem; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
  .row > :global(section), .right > :global(section) { background: var(--panel); border-radius: 10px; padding: 0.8rem; }
  .center { text-align: center; margin-top: 30vh; }
  @media (max-width: 900px) {
    main, .row { grid-template-columns: 1fr; }
  }
</style>
