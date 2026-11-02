<script lang="ts">
  // Who is using the editor, where else it can be opened, and the password (ADR-026).
  import { onMount } from 'svelte'
  import { ApiError, changePassword, loadAccess, signOut, type AccessState } from '../lib/api'
  import { t } from '../lib/i18n'
  import { generatePassword } from '../lib/password'

  let { onClose, onSignedOut }: { onClose: () => void; onSignedOut: () => void } = $props()

  let access = $state<AccessState | null>(null)
  let current = $state('')
  let next = $state('')
  let shown = $state(false)
  let message = $state('')
  let error = $state('')
  let busy = $state(false)

  const refresh = async () => (access = await loadAccess())
  onMount(() => void refresh())

  function generate() {
    next = generatePassword()
    shown = true
    message = t('access.generated', { password: next })
  }

  async function save(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = message = ''
    try {
      await changePassword(current, next)
      message = `${t('access.saved')} ${t('access.restart')}`
      current = next = ''
      await refresh()
    } catch (failure) {
      const code = failure instanceof ApiError ? failure.code : undefined
      error = code ? t(`access.error.${code}` as 'access.error.too_short') : (failure as Error).message
    } finally {
      busy = false
    }
  }

  async function leave() {
    await signOut()
    onSignedOut()
  }
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && onClose()} />

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="backdrop" onclick={(e) => e.target === e.currentTarget && onClose()}>
  <div class="dialog" role="dialog" aria-modal="true" aria-label={t('access.title')}>
    <header>
      <strong>{t('access.title')}</strong>
      <span class="spacer"></span>
      <button onclick={onClose}>{t('access.close')}</button>
    </header>
    {#if access}
      <div class="body">
        <p>{access.remote ? t('access.remote') : t('access.here')}</p>
        {#if access.addresses.length}
          <p>{t('access.addresses')}</p>
          <ul>{#each access.addresses as address (address)}<li><code>{address}</code></li>{/each}</ul>
        {:else if access.can_browse}
          <p class="muted">{t('access.no_addresses')}</p>
        {/if}
        <p class="muted">{access.password_set ? t('access.password_set') : t('access.password_unset')}</p>
        <form onsubmit={save}>
          {#if access.password_set}
            <input type="password" bind:value={current} placeholder={t('access.current')} aria-label={t('access.current')} autocomplete="current-password" />
          {/if}
          <div class="row">
            <input type={shown ? 'text' : 'password'} bind:value={next} placeholder={t('access.new')} aria-label={t('access.new')} autocomplete="new-password" />
            <button type="button" onclick={generate}>{t('access.generate')}</button>
            <label class="muted"><input type="checkbox" bind:checked={shown} /> {t('access.show')}</label>
          </div>
          <button class="primary" disabled={busy || !next || (access.password_set && !current)}>{t('access.save')}</button>
        </form>
        {#if message}<p class="ok" role="status">{message}</p>{/if}
        {#if error}<p class="error" role="alert">{error}</p>{/if}
        {#if access.remote}<button onclick={leave}>{t('access.sign_out')}</button>{/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .backdrop { position: fixed; inset: 0; background: #000a; display: grid; place-items: center; z-index: 50; }
  .dialog { width: min(30rem, 94vw); max-height: 85vh; overflow-y: auto; background: var(--panel); border-radius: 12px; }
  header { display: flex; align-items: center; gap: 0.5rem; padding: 0.7rem 1rem; border-bottom: 1px solid var(--line); }
  .spacer { flex: 1; }
  .body { display: grid; gap: 0.7rem; padding: 1rem; }
  p, ul { margin: 0; }
  ul { padding-left: 1.2rem; }
  code { overflow-wrap: anywhere; }
  form { display: grid; gap: 0.6rem; }
  .row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  .row input[type='password'], .row input[type='text'] { flex: 1; min-width: 10rem; }
  .ok { color: var(--accent); overflow-wrap: anywhere; }
</style>
