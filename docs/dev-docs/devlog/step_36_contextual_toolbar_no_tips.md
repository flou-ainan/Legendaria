# Step 36 — Contextual toolbar, tips removed

**Date:** 2026-10-27
**Agent/author:** Claude Code (Sonnet 5.5), with flou-ainan
**Related:** plan 08 (step 1)

## What was done

- **Tips removed:** the two permanent hint lines (under the timeline title and in the empty editor box) took space; the owner will have an interactive tutorial after the MVP (plan 08, "After the MVP"). The block editor now takes no room until a block is selected.
- **Contextual toolbar:** no block selected = Play, In, Out, Cut, Look; a block selected = Play, Split, Merge, Delete, Look. Snap, Undo and Redo stay as a utility group. Split, Merge and Delete left the block editor, which now only holds the text and the times.
- **Deselect:** Esc (shortcut `deselect` in `shortcuts.json`) or a click on the empty waveform.
- **Layout:** the block editor moved under the timeline, because it appears on selection and would otherwise push the timeline down under the pointer (the double-click test caught it).

## Files touched

`Toolbar.svelte`, `Inspector.svelte`, `Timeline.svelte`, `Player.svelte`, `App.svelte`, `lib/shortcuts.json`, both locales (removed `timeline.hint` and `inspector.hint`; added `tool.merge_short`, `tool.delete_short`), `e2e/smoke.mjs`, plan 08, `PROJECT.md`, `chat-context.md`.

## How it was tested

svelte-check clean, Vitest 11, `npm run e2e` (new checks: Merge shown and Cut hidden with a block selected; Esc swaps them back).
Not covered: touch use of the contextual toolbar on a phone.
