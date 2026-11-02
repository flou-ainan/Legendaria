# Step 37 — Timeline touch fix, real magnet, Solar icons, Undo/Redo first

**Date:** 2026-10-27
**Agent/author:** Claude Code (Sonnet 5.5), with flou-ainan
**Related:** plan 08; ADR-020

## What was done

- **Only the selected block moves or resizes** (`Timeline.svelte`). Every block was draggable, so on a phone any swipe over the timeline moved or resized blocks. Now `drag` and `resize` are on only for the selected block; the others also get `touch-action: pan-x pan-y` so the browser scrolls instead. A click selects first, then a drag works. This also applies on the desktop.
- **Magnet that follows the pointer.** wavesurfer moves a block by the pointer's change since the last event; snapping moved the block too, so the next small movement was added to the snapped position and snapped back: the block stayed stuck far from the pointer. The component now keeps the position the pointer asked for (`raw`) apart from the position drawn. The block sticks to a target while the pointer is within 8 px of it and follows the pointer again once it leaves, like Inkscape or Kdenlive.
- **Undo and Redo are the first buttons** of the toolbar.
- **Solar Linear icons** in the toolbar instead of emoji (ADR-020): `lib/icons.ts`, `components/Icon.svelte`; credit (CC BY 4.0) in both READMEs.

## Files touched

`Timeline.svelte`, `Toolbar.svelte`, new `Icon.svelte` and `lib/icons.ts`, `e2e/smoke.mjs`, both READMEs, ADR-020, plan 08, `PROJECT.md`, `chat-context.md`.

## How it was tested

svelte-check clean, Vitest 11, `npm run build` then `npm run e2e`: a drag on an unselected block changes nothing; after selecting, the edge sticks to the next block (guide line), follows the pointer when it moves 100 px away, and sticks again when it comes back.

Not tested: touch on a real phone (the `touch-action` and selection rule follow the wavesurfer source, but no device was used).
