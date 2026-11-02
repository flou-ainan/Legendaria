# Step 38 — Playhead arrow and centred mode, settings.json, minimal toolbar

**Date:** 2026-10-27
**Agent/author:** Claude Code (Sonnet 5.5), with flou-ainan
**Related:** plan 08; ADR-021

## What was done

- **`settings.json`** (basic / advanced) with the snap distance now 4 px, autosave, undo and zoom values; wired into `editor.svelte.ts` and `Timeline.svelte`.
- **Toolbar:** the text under the icons is gone (the names stay as tooltips); selected buttons have dark icons on the yellow background.
- **Playhead:** a draggable arrow (pointer devices) and a centred playhead with a sliding timeline and empty space before the start (touch screens), chosen by `settings.playhead` (ADR-021).
- e2e updated for the 4 px magnet (it aims 3 px from the next block) and the toolbar names.

## Files touched

`lib/settings.json`, `lib/settings.ts`, `Timeline.svelte`, `Toolbar.svelte`, `editor.svelte.ts`, `e2e/smoke.mjs`, ADR-021, `PROJECT.md`, plan 08, `chat-context.md`.

## How it was tested

svelte-check clean, `npm run e2e`: dragging the arrow seeks; in a touch-emulated page the margin is half a screen, setting the video time scrolls the timeline, and scrolling it seeks. Screenshot checked. Not tested on a real phone (touch inertia, pinch zoom).
