<script lang="ts">
  // Quick menu for the subtitle look: position, size, font, colours, outline, the rounded rectangle and caps.
  // It edits the whole track (the project `look`, ADR-019) or, with a block selected and "This subtitle"
  // chosen, only that cue (`cue.look`, ADR-022). Values shown: cue → track → style.
  import { editor } from '../lib/editor.svelte'
  import type { BaseLook, Look } from '../lib/api'
  import { t } from '../lib/i18n'

  const TOP = 0.88
  const BOTTOM = 0.1

  let scope = $state<'track' | 'cue'>('track')
  const cue = $derived(editor.project?.cues[editor.selected])
  const forCue = $derived(scope === 'cue' && !!cue)
  const track = $derived(editor.project?.look ?? {})
  const own = $derived<Look>(forCue ? (cue!.look ?? {}) : track) // what this scope overrides
  const value = <K extends keyof BaseLook>(key: K): BaseLook[K] =>
    ((forCue ? cue!.look?.[key] : undefined) ?? track[key] ?? editor.base[key]) as BaseLook[K]
  const set = (patch: { [K in keyof Look]?: Look[K] | null }) =>
    forCue ? editor.setCueLook(editor.selected, patch) : editor.setLook(patch)

  const y = $derived(value('y'))
  const size = $derived(own.size ?? 1) // a cue's size is relative to the track
  const font = $derived(own.font ?? '')
  const color = $derived(value('color'))
  const outline = $derived(value('outline_color'))
  const box = $derived(value('box'))
  const upper = $derived(value('uppercase'))
  const percent = (key: keyof BaseLook) => Math.round(Number(value(key)) * 100)
</script>

<div class="look" role="group" aria-label={t('look.title')}>
  <p class="heading">{t('look.heading')}</p>
  {#if cue}
    <div class="row scope" role="radiogroup" aria-label={t('look.scope')}>
      <button role="radio" aria-checked={!forCue} class:on={!forCue} onclick={() => (scope = 'track')}>{t('look.scope_track')}</button>
      <button role="radio" aria-checked={forCue} class:on={forCue} onclick={() => (scope = 'cue')}>{t('look.scope_cue')}</button>
    </div>
  {/if}
  {#if forCue}
    <button class="all" onclick={() => editor.applyToAll(editor.selected)} disabled={!Object.keys(own).length}>{t('look.apply_all')}</button>
  {/if}
  <div class="row presets">
    <button onclick={() => set({ y: TOP })} class:on={Math.abs(y - TOP) < 0.005}>⤒ {t('look.top')}</button>
    <button onclick={() => set({ y: BOTTOM })} class:on={Math.abs(y - BOTTOM) < 0.005}>⤓ {t('look.bottom')}</button>
    <button onclick={() => set(Object.fromEntries(Object.keys(own).map((k) => [k, null])))} disabled={!Object.keys(own).length}>{t('look.reset')}</button>
  </div>
  <label>{t('look.height')} <output>{Math.round(y * 100)}%</output>
    <input type="range" min="0" max="100" value={Math.round(y * 100)} oninput={(e) => set({ y: Number(e.currentTarget.value) / 100 })} />
  </label>
  <label>{t('look.size')} <output>{Math.round(size * 100)}%</output>
    <input type="range" min="40" max="250" value={Math.round(size * 100)} oninput={(e) => set({ size: Number(e.currentTarget.value) / 100 })} />
  </label>
  <label>{t('look.font')}
    <select value={font} onchange={(e) => set({ font: e.currentTarget.value || null })}>
      <option value="">{forCue ? t('look.font_track', { font: track.font ?? editor.base.font }) : t('look.font_style', { font: editor.base.font })}</option>
      {#each editor.fonts as f (f.file)}<option value={f.family} style="font-family: '{f.family}'">{f.family} · {t(`font.${f.category}` as 'font.sans')}</option>{/each}
    </select>
  </label>
  <div class="row colors">
    <label>{t('look.color')}
      <input type="color" value={color} oninput={(e) => set({ color: e.currentTarget.value })} />
    </label>
    <label>{t('look.outline')}
      <input type="color" value={outline} oninput={(e) => set({ outline_color: e.currentTarget.value })} />
    </label>
  </div>
  <label>{t('look.outline_width')} <output>{Math.round(Number(value('outline')))} px</output>
    <input type="range" min="0" max="20" step="0.5" value={value('outline')} oninput={(e) => set({ outline: Number(e.currentTarget.value) })} />
  </label>
  <label class="check"><input type="checkbox" checked={value('shadow_on')} onchange={(e) => set({ shadow_on: e.currentTarget.checked })} /> {t('look.shadow')}</label>
  {#if value('shadow_on')}
    <div class="boxed">
      <label>{t('look.shadow_color')}
        <input type="color" value={value('shadow_color')} oninput={(e) => set({ shadow_color: e.currentTarget.value })} />
      </label>
      <label>{t('look.shadow_size')} <output>{Math.round(Number(value('shadow')))} px</output>
        <input type="range" min="0" max="20" step="0.5" value={value('shadow')} oninput={(e) => set({ shadow: Number(e.currentTarget.value) })} />
      </label>
      <label>{t('look.shadow_intensity')} <output>{percent('shadow_opacity')}%</output>
        <input type="range" min="0" max="100" value={percent('shadow_opacity')} oninput={(e) => set({ shadow_opacity: Number(e.currentTarget.value) / 100 })} />
      </label>
    </div>
  {/if}
  <label class="check"><input type="checkbox" checked={upper} onchange={(e) => set({ uppercase: e.currentTarget.checked })} /> {t('look.uppercase')}</label>
  <label class="check"><input type="checkbox" checked={box} onchange={(e) => set({ box: e.currentTarget.checked })} /> {t('look.box')}</label>
  {#if box}
    <div class="boxed">
      <label>{t('look.box_color')}
        <input type="color" value={value('box_color')} oninput={(e) => set({ box_color: e.currentTarget.value })} />
      </label>
      <label>{t('look.box_transparency')} <output>{100 - percent('box_opacity')}%</output>
        <input type="range" min="0" max="100" value={100 - percent('box_opacity')} oninput={(e) => set({ box_opacity: 1 - Number(e.currentTarget.value) / 100 })} />
      </label>
      <label>{t('look.box_width')} <output>{percent('box_padding_x')}%</output>
        <input type="range" min="0" max="200" value={percent('box_padding_x')} oninput={(e) => set({ box_padding_x: Number(e.currentTarget.value) / 100 })} />
      </label>
      <label>{t('look.box_height')} <output>{percent('box_padding_y')}%</output>
        <input type="range" min="0" max="100" value={percent('box_padding_y')} oninput={(e) => set({ box_padding_y: Number(e.currentTarget.value) / 100 })} />
      </label>
      <label>{t('look.box_radius')} <output>{percent('box_radius')}%</output>
        <input type="range" min="0" max="100" value={percent('box_radius')} oninput={(e) => set({ box_radius: Number(e.currentTarget.value) / 100 })} />
      </label>
    </div>
  {/if}
</div>

<style>
  .look { display: grid; gap: 0.7rem; min-width: min(18rem, 80vw); max-height: 70vh; overflow-y: auto; }
  .boxed { display: grid; gap: 0.7rem; padding-left: 0.8rem; border-left: 2px solid var(--line); }
  .all { width: 100%; }
  .scope button { font-size: 0.85rem; }
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
