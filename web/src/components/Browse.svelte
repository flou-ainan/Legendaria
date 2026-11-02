<script lang="ts">
  // A small file browser over the computer running `flosub serve` (a browser cannot tell us a
  // file's path, so we list the folders here instead and open the file in place, with no copy).
  import { onMount } from 'svelte'
  import { browse, type Listing } from '../lib/api'
  import { t } from '../lib/i18n'

  let { onPick, onClose }: { onPick: (path: string) => void; onClose: () => void } = $props()

  let listing = $state<Listing | null>(null)
  let error = $state('')
  let typed = $state('')

  async function go(path?: string) {
    try {
      listing = await browse(path)
      typed = listing.path
      error = ''
    } catch (e) {
      error = (e as Error).message
    }
  }

  onMount(() => go())

  function join(folder: string, name: string) {
    return folder + (folder.includes('\\') ? '\\' : '/') + name
  }

  const size = (bytes: number) => (bytes > 1e9 ? `${(bytes / 1e9).toFixed(1)} GB` : `${Math.round(bytes / 1e6)} MB`)
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && onClose()} />

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="backdrop" onclick={onClose}>
  <div class="dialog" role="dialog" tabindex="-1" aria-label={t('browse.title')} onclick={(e) => e.stopPropagation()}>
    <header>
      <strong>{t('browse.title')}</strong>
      <span class="spacer"></span>
      <button onclick={onClose}>✕</button>
    </header>
    {#if listing}
      <div class="path">
        <button disabled={!listing.parent} onclick={() => go(listing!.parent!)}>↑ {t('browse.up')}</button>
        <button onclick={() => go(listing!.home)}>⌂ {t('browse.home')}</button>
        <input class="typed" bind:value={typed} onchange={() => go(typed)} aria-label={t('browse.path')} />
      </div>
      <ul>
        {#each listing.entries as entry (entry.name)}
          <li>
            <button class="entry" onclick={() => (entry.dir ? go(join(listing!.path, entry.name)) : onPick(join(listing!.path, entry.name)))}>
              <span>{entry.dir ? '📁' : entry.name.endsWith('.legendaria.json') ? '📝' : '🎞'} {entry.name}</span>
              {#if !entry.dir}<span class="muted">{size(entry.size)}</span>{/if}
            </button>
          </li>
        {:else}
          <li class="muted pad">{t('browse.empty')}</li>
        {/each}
      </ul>
    {/if}
    {#if error}<p class="error pad">{error}</p>{/if}
  </div>
</div>

<style>
  .backdrop { position: fixed; inset: 0; background: #000a; display: grid; place-items: center; z-index: 50; }
  .dialog { width: min(40rem, 94vw); max-height: 85vh; display: flex; flex-direction: column; background: var(--panel); border-radius: 12px; overflow: hidden; }
  header { display: flex; align-items: center; gap: 0.5rem; padding: 0.7rem 1rem; border-bottom: 1px solid var(--line); }
  .spacer { flex: 1; }
  .path { display: flex; gap: 0.5rem; align-items: center; padding: 0.6rem 1rem; flex-wrap: wrap; }
  .typed { flex: 1; min-width: 12rem; }
  ul { list-style: none; margin: 0; padding: 0 0.5rem 0.5rem; overflow-y: auto; }
  .entry { display: flex; justify-content: space-between; width: 100%; text-align: left; background: none; padding: 0.55rem 0.6rem; }
  .entry:hover { background: var(--line); }
  .pad { padding: 1rem; }
</style>
