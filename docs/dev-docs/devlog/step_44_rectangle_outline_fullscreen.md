# Step 44 — Rounded rectangle, outline colour and thickness, full screen with subtitles

**Date:** 2026-10-27
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related:** ADR-019 (update), plan 08

## Owner's report and what was done

- **Rectangle with little horizontal padding, square corners; no way to change its colour, size, transparency or roundness; outline did not take its colour.** All came from ASS `BorderStyle 3`, which draws the box from the outline settings. The box is now a drawn, rounded shape under the text (ADR-019 update), with its own colour, transparency, extra width, extra height and roundness in the Look menu. The text outline keeps its colour and gets a thickness slider (0–20 px).
- **Subtitles disappeared in full screen:** the `<video>`'s own full screen leaves JASSUB's canvas behind. The native button is hidden (`controlslist="nofullscreen"`); a button on the video (also double-click and `F`) puts the box holding the video and the canvas in full screen. iPhones only allow the video itself, so there the subtitles still do not show.
- **"Edit all subtitles at once" → "Edit this track's subtitles"**; multiple tracks with their own look are noted in plan 08.
- `server.API_VERSION` 3 (the page warns if the running server is older).

## Files touched

engine: `fonts.py` (`find_font` moved here, `metrics_for`, `text_width`, `FontMetrics`), `ass.py` (`box_shape`, new look keys), `project.py`, `server.py`, `schemas/project.schema.json`, tests. web: `LookMenu.svelte`, `Player.svelte`, `api.ts`, `editor.svelte.ts`, `icons.ts`, `shortcuts.json`, locales, `e2e/smoke.mjs`. Docs: ADR-019, plan 08, `PROJECT.md`, `chat-context.md`.

## How it was tested

134 pytest (rounded shape on layer 0 with its colour, outline colour kept, the box grows with the text and the padding, clamping). svelte-check, Vitest 11, e2e (outline and rectangle colours, roundness 0 gives square corners, full screen holds the canvas at full width). Rendered frames with FFmpeg for three fonts; a screenshot of the browser preview.
