<script lang="ts">
  // Quick menu for the look of a subtitle track as a whole (today there is one track): position, size, font,
  // colours, outline, the rounded rectangle and caps. Every value is a project `look` override (ADR-019).
  import { editor } from '../lib/editor.svelte'
  import type { BaseLook } from '../lib/api'
  import { t } from '../lib/i18n'

  const TOP = 0.88
  const BOTTOM = 0.1

  const look = $derived(editor.project?.look ?? {})
  const y = $derived(look.y ?? editor.base.y)
  const size = $derived(look.size ?? 1)
  const font = $derived(look.font ?? '')
  // the project's override, else what the style sets
  const value = <K extends keyof BaseLook>(key: K): BaseLook[K] => (look[key] ?? editor.base[key]) as BaseLook[K]
  const color = $derived(value('color'))
  const outline = $derived(value('outline_color'))
  const box = $derived(value('box'))
  const upper = $derived(value('uppercase'))
  const percent = (key: keyof BaseLook) => Math.round(Number(value(key)) * 100)
</script>

<div class="look" role="group" aria-label={t('look.title')}>
  <p class="heading">{t('look.heading')}</p>
  <div class="row presets">
    <button onclick={() => editor.setLook({ y: TOP })} class:on={Math.abs(y - TOP) < 0.005}>⤒ {t('look.top')}</button>
    <button onclick={() => editor.setLook({ y: BOTTOM })} class:on={Math.abs(y - BOTTOM) < 0.005}>⤓ {t('look.bottom')}</button>
    <button onclick={() => editor.setLook(Object.fromEntries(Object.keys(look).map((k) => [k, null])))} disabled={!Object.keys(look).length}>{t('look.reset')}</button>
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
  <div class="row colors">
    <label>{t('look.color')}
      <input type="color" value={color} oninput={(e) => editor.setLook({ color: e.currentTarget.value })} />
    </label>
    <label>{t('look.outline')}
      <input type="color" value={outline} oninput={(e) => editor.setLook({ outline_color: e.currentTarget.value })} />
    </label>
  </div>
  <label>{t('look.outline_width')} <output>{Math.round(Number(value('outline')))} px</output>
    <input type="range" min="0" max="20" step="0.5" value={value('outline')} oninput={(e) => editor.setLook({ outline: Number(e.currentTarget.value) })} />
  </label>
  <label class="check"><input type="checkbox" checked={upper} onchange={(e) => editor.setLook({ uppercase: e.currentTarget.checked })} /> {t('look.uppercase')}</label>
  <label class="check"><input type="checkbox" checked={box} onchange={(e) => editor.setLook({ box: e.currentTarget.checked })} /> {t('look.box')}</label>
  {#if box}
    <div class="boxed">
      <label>{t('look.box_color')}
        <input type="color" value={value('box_color')} oninput={(e) => editor.setLook({ box_color: e.currentTarget.value })} />
      </label>
      <label>{t('look.box_transparency')} <output>{100 - percent('box_opacity')}%</output>
        <input type="range" min="0" max="100" value={100 - percent('box_opacity')} oninput={(e) => editor.setLook({ box_opacity: 1 - Number(e.currentTarget.value) / 100 })} />
      </label>
      <label>{t('look.box_width')} <output>{percent('box_padding_x')}%</output>
        <input type="range" min="0" max="200" value={percent('box_padding_x')} oninput={(e) => editor.setLook({ box_padding_x: Number(e.currentTarget.value) / 100 })} />
      </label>
      <label>{t('look.box_height')} <output>{percent('box_padding_y')}%</output>
        <input type="range" min="0" max="100" value={percent('box_padding_y')} oninput={(e) => editor.setLook({ box_padding_y: Number(e.currentTarget.value) / 100 })} />
      </label>
      <label>{t('look.box_radius')} <output>{percent('box_radius')}%</output>
        <input type="range" min="0" max="100" value={percent('box_radius')} oninput={(e) => editor.setLook({ box_radius: Number(e.currentTarget.value) / 100 })} />
      </label>
    </div>
  {/if}
</div>

<style>
  .look { display: grid; gap: 0.7rem; min-width: min(18rem, 80vw); max-height: 70vh; overflow-y: auto; }
  .boxed { display: grid; gap: 0.7rem; padding-left: 0.8rem; border-left: 2px solid var(--line); }
  .heading { margin: 0; font-size: 0.85rem; color: var(--text); }
  .row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
  .row button { flex: 1; }
  .row .on { background: var(--accent); color: #15131c; }
  label { display: grid; gap: 0.25rem; font-size: 0.8rem; color: var(--muted); }
  .colors label { flex: 1; }
  input[type='color'] { width: 100%; height: 2rem; padding: 0; border: 1px solid var(--line); background: none; }
  .check { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: var(--text); }
  output { float: right; color: var(--text); }
  input[type='range'] { width: 100%; accent-color: var(--accent); }
</style>
