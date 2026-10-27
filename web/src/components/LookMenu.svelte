<script lang="ts">
  // Quick menu for the subtitle look as a whole: height and size sliders, Top / Bottom presets, font.
  import { editor } from '../lib/editor.svelte'
  import { t } from '../lib/i18n'

  const TOP = 0.88
  const BOTTOM = 0.1

  const look = $derived(editor.project?.look ?? {})
  const y = $derived(look.y ?? editor.base.y)
  const size = $derived(look.size ?? 1)
  const font = $derived(look.font ?? '')
</script>

<div class="look" role="group" aria-label={t('look.title')}>
  <div class="row presets">
    <button onclick={() => editor.setLook({ y: TOP })} class:on={Math.abs(y - TOP) < 0.005}>⤒ {t('look.top')}</button>
    <button onclick={() => editor.setLook({ y: BOTTOM })} class:on={Math.abs(y - BOTTOM) < 0.005}>⤓ {t('look.bottom')}</button>
    <button onclick={() => editor.setLook({ y: null, size: null, font: null })} disabled={!Object.keys(look).length}>{t('look.reset')}</button>
  </div>
  <label>{t('look.height')} <output>{Math.round(y * 100)}%</output>
    <input type="range" min="0" max="100" value={Math.round(y * 100)} oninput={(e) => editor.setLook({ y: Number(e.currentTarget.value) / 100 })} />
  </label>
  <label>{t('look.size')} <output>{Math.round(size * 100)}%</output>
    <input type="range" min="40" max="250" value={Math.round(size * 100)} oninput={(e) => editor.setLook({ size: Number(e.currentTarget.value) / 100 })} />
  </label>
  <label>{t('look.font')}
    <select value={font} onchange={(e) => editor.setLook({ font: e.currentTarget.value || null })}>
      <option value="">{t('look.font_style', { font: editor.base.font })}</option>
      {#each editor.fonts as f (f.file)}<option value={f.family} style="font-family: '{f.family}'">{f.family} · {t(`font.${f.category}` as 'font.sans')}</option>{/each}
    </select>
  </label>
</div>

<style>
  .look { display: grid; gap: 0.7rem; min-width: min(18rem, 80vw); }
  .row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
  .row button { flex: 1; }
  .row .on { background: var(--accent); color: #15131c; }
  label { display: grid; gap: 0.25rem; font-size: 0.8rem; color: var(--muted); }
  output { float: right; color: var(--text); }
  input[type='range'] { width: 100%; accent-color: var(--accent); }
</style>
