<script lang="ts">
  // The page a phone sees before it has given the access password (ADR-026).
  import { ApiError, signIn } from '../lib/api'
  import { t } from '../lib/i18n'

  let { onDone, expired = false }: { onDone: () => void; expired?: boolean } = $props()

  let password = $state('')
  let error = $state('')
  let busy = $state(false)

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      await signIn(password)
      onDone()
    } catch (failure) {
      const api = failure instanceof ApiError ? failure : null
      error = api?.code === 'too_many' ? t('signin.too_many', { seconds: api.retryAfter ?? 60 }) : api?.code === 'wrong_password' ? t('signin.wrong') : (failure as Error).message
      password = ''
    } finally {
      busy = false
    }
  }
</script>

<section class="card">
  <img class="logo" src="/logo.svg" alt="" />
  <h1>{t('signin.title')}</h1>
  <p class="muted">{expired ? t('signin.expired') : t('signin.intro')}</p>
  <form onsubmit={submit}>
    <!-- svelte-ignore a11y_autofocus -->
    <input type="password" bind:value={password} placeholder={t('signin.password')} aria-label={t('signin.password')} autocomplete="current-password" autofocus />
    <button class="primary" disabled={busy || !password}>{t('signin.button')}</button>
  </form>
  {#if error}<p class="error" role="alert">{error}</p>{/if}
</section>

<style>
  .card { max-width: 26rem; margin: 12vh auto 0; padding: 1.5rem; background: var(--panel); border-radius: 12px; display: grid; gap: 0.8rem; justify-items: center; text-align: center; }
  .logo { width: 3rem; height: 3rem; }
  h1 { margin: 0; font-size: 1.3rem; }
  form { display: grid; gap: 0.6rem; width: 100%; }
  p { margin: 0; }
</style>
