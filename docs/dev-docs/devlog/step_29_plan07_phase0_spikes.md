# Step 29 — Plan 07 phase 0: study spikes

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_07_web_editor.md

## What was done

The four study spikes from plan 07 ran outside the repository, in `../legendaria-spikes/`, because they use the owner's media.

- **1.1 OpenReel:** 460k lines of TS, built around WebCodecs compositing. For a single video, `<video>` + JASSUB is enough, so we take patterns from it, not code.
- **1.2 JASSUB:** matches FFmpeg's libass frame by frame, including the pop animation. It needs a production build, COOP/COEP headers and the fonts served to it.
- **1.3 wavesurfer.js:** handles 500 cue regions on a 10-minute track. Peaks computed on the server load in 53 ms and use 9 MB of JS heap. Dragging edges and splitting work.
- **1.4 FFmpeg:** cut and burn run in one pass (`trim`/`concat` + `ass`) with a cue remap. 14.5 s rendered in 8 s, and sync was verified after each cut.

The framework comparison for ADR-015 recommends Svelte 5, with Vue 3 second. Plan 07 now records the owner's answers (lean MVP; the backend is always present) and a "Later" list.

## Files

- New: `docs/dev-docs/references/plan07_phase0_spikes.md`.
- Changed: `docs/dev-docs/planning/plan_07_web_editor.md`, `docs/PROJECT.md`.

## How it was tested

The spike code lives outside the repo:
- remap pytest: 4 passed;
- Playwright with headless Chrome for the JASSUB frame captures and the wavesurfer benchmarks;
- a pixel diff against FFmpeg (`compare.py`);
- `ffprobe` for the duration of the cut output.
