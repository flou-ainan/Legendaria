# Step 45 — Style for one subtitle or the whole track

**Date:** 2026-10-27
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related:** plan 09, ADR-022, plan 08

## What was done

- **Engine:** `Cue.look` (optional, cleaned like the project look), saved only when set; cut remap keeps it; schema allows it on cues. `to_ass` resolves style → track → cue and writes one `Style:` line per distinct look (`Default`, `Cue1`…), with each cue's own position, rectangle and animation (`style_fields` split out).
- **Editor:** `setCueLook`, `applyToAll` (a cue's size multiplies into the track's), split copies the look to both halves, merge keeps the first one's. The Look menu shows "Whole track | This subtitle" when a block is selected (default: whole track), and "Apply to all" in the cue scope. The timeline marks blocks with their own style with ✦.

## Files touched

engine: `cues.py`, `project.py`, `ass.py`, `schemas/project.schema.json`, `tests/test_project.py`. web: `LookMenu.svelte`, `editor.svelte.ts`, `api.ts`, `Timeline.svelte`, locales, `e2e/smoke.mjs`. Docs: plan 09 (new), ADR-022 (new), plan 08, `PROJECT.md`, `chat-context.md`.

## How it was tested

135 pytest (cue look cleaned, saved, schema-valid, kept by remap, its own `Style:` line). svelte-check, Vitest 11, e2e: select a block, "This subtitle", change the colour (only that cue changes, `Cue1` style in the preview, ✦ on the block), then "Apply to all" (the track takes the colour, the cue's look goes away).

Not covered: a cue look with the rectangle and a different size burned with FFmpeg (same code path as the track look, checked in step 44).
