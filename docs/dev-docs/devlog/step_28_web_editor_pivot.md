# Step 28 — Pivot to a web editor; Blender add-on frozen

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

After the manual test (KI-001 freeze, hard-to-edit strips), the owner decided to stop investing in Blender. The new direction is a lean browser editor: cut the video, edit the subtitles, export a burned MP4 or SRT / VTT / ASS.

- A panoramic research pass covered:
  - OpenReel Video (MIT, TS + React + Vite, its timeline and trim logic as a reuse candidate; its ffmpeg.wasm core is GPL and is avoided);
  - JASSUB (libass in WASM, for an exact live preview);
  - wavesurfer.js (BSD-3, waveform and regions);
  - Aegisub (BSD-3, timing ideas).
- Docs:
  - new plan 07 (research summary, architecture, phases: study spikes → decisions → MVP → Blender freeze);
  - new ADR-014 (web editor main UI, add-on frozen, ADR-013 suspended).
  - Plans 05 and 06 are marked superseded. ADR-002 is superseded and ADR-013 suspended.
  - `PROJECT.md` and the known issues are updated.

No code changed.

## Files

- New: `docs/dev-docs/planning/plan_07_web_editor.md`, `docs/dev-docs/decisions/ADR-014-web-editor-blender-frozen.md`.
- Changed: plans 05 and 06 (status), ADR-002 and ADR-013 (status), `docs/PROJECT.md`, `docs/dev-docs/known-issues.md`, `CHANGELOG.md`.

## How it was tested

Docs only. Links checked by hand.
