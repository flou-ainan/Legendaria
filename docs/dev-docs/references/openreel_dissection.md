# OpenReel Video: what we take for the web editor

**Date:** 2026-10-27
**Source:** https://github.com/Augani/openreel-video (MIT), commit `367d7e9` (2026-10-17), cloned outside the repo.
**Related:** plan 07, ADR-015, `plan07_phase0_spikes.md` (spike 1.1)

We take **patterns, not code**: no file is copied. If a file is ever copied, keep its MIT notice and record it in the devlog.

## Adopt

### 1. Undo with auto-grouping (`packages/core/src/actions/action-history.ts`)

- **How OpenReel does it:**
  - every edit pushes an entry (action + inverse);
  - `beginGroup`/`endGroup` bundle multi-step edits;
  - rapid edits of the **same type on the same target** within a short window merge into one undo step, so a drag or a slider is undone in one step. Creation and deletion never merge.
  - A new edit clears the redo stack, and the history is capped (1,000 entries).
- **Ours:** our project document is small (cues + kept ranges), so we store **snapshots** instead of inverse actions. That is simpler and cannot get out of sync. We keep the same rules: auto-grouping (same kind + same cue within ~500 ms), explicit groups, a cap and redo clearing.

### 2. Snapping (`packages/core/src/timeline/clip-manager.ts`)

- **How OpenReel does it:**
  - the threshold is in **pixels**, converted to time with the zoom (`threshold_px / pixelsPerSecond`), so snapping feels the same at any zoom;
  - the snap goes to the closest of the targets: the grid, the start or end of a clip on the same track, or the playhead;
  - it returns which target won, which is useful for a visual hint.
- **Ours:** the targets are the neighbor cue edges, the cut edges and the playhead, plus **word boundaries from the transcript**. Snapping to the moment a word starts or ends is something OpenReel cannot offer. Scene changes come later (plan 07, "Later"). The `N` key toggles snapping.

### 3. Data-driven keyboard shortcuts (`apps/web/src/services/keyboard-shortcuts.ts`)

- **How OpenReel does it:**
  - one table with `id`, `name`, `description`, `category`, `defaultKey` and `currentKey`;
  - rebinding with a conflict check;
  - `?` shows an overlay listing them.
- **Ours:** the same table, but the defaults live in a **JSON config file** (hackable, ADR-006), and the names go through i18n. The starting set is a subset of theirs, all of them standard in video editors:

| Key | Action |
|---|---|
| Space | play / pause |
| ← / → | one frame back / forward |
| Shift+← / → | one second back / forward |
| Home / End | start / end |
| [ / ] | previous / next cue |
| I / O | mark the in / out point of a range to cut |
| S | split the cue at the playhead |
| Q / W | move the cue's start / end to the playhead |
| Delete / Shift+Delete | delete the cue / remove the range and close the gap |
| Ctrl+Z / Ctrl+Shift+Z | undo / redo |
| N | snapping on/off |
| Ctrl+= / Ctrl+− / Ctrl+0 | zoom in / out / fit |
| Ctrl+S / Ctrl+E | save the project / export |
| ? | show the shortcuts |

### 4. Timeline zoom and scrolling (`apps/web/src/components/editor/Timeline.tsx`)

- **Ctrl+wheel zooms around the pointer:** the time under the cursor stays fixed (`scrollLeft = timeAtCursor * newPps − pointerX`), with a 1.12× step clamped between a min and a max.
- **Shift+wheel** scrolls horizontally.
- **During playback**, the view follows the playhead only when it leaves the visible area.
- wavesurfer.js has a zoom of its own. We drive it with these rules so that the waveform, the cue track and the cut track move together.

### 5. A versioned, validated project file (`packages/core/src/editing/portable-project.ts`, `safe-json.ts`)

- **How OpenReel does it:**
  - the file is tagged `"format": "openreel-edit"` and `"version": 2`;
  - a schema validates it on load: numeric ranges, enums, maximum array sizes and string patterns, so a bad or hostile file is rejected cleanly.
  - A clip refers to its media through `inPoint`/`outPoint`.
- **Ours (input for ADR-016):** `"format": "legendaria-project"`, `"version": 1`, validated with JSON Schema (the engine already uses `jsonschema`). The kept ranges are `inPoint`/`outPoint` pairs over the single source video.

### 6. Property-based tests

- **How OpenReel does it:** timeline operations are tested with fast-check (random inputs that must keep invariants).
- **Ours:** test the remap and the cut list this way:
  - Hypothesis in Python, fast-check in TS;
  - invariants: the output duration equals the sum of the kept ranges, cues never overlap a removed range, and no cuts gives the same cues back.

## Not adopted (and why)

- **Decoding, frame cache, WebGPU effects and compositing** (`video/`, `media/mediabunny-engine.ts`, `playback/`): we play one source video, so `<video>` does all of this.
- **The master clock** (`playback/master-timeline-clock.ts`): the `<video>` is the clock (`requestVideoFrameCallback`).
- **Waveform generation** (`media/waveform-*`): server peaks + wavesurfer.js (spike 1.3).
- **WebCodecs export, and ffmpeg.wasm** (which is GPL with libass/x264): export runs on the server with native FFmpeg.
- **Their subtitle model** (`text/subtitle-engine.ts`): our cues JSON + `.ass` are richer, and they already exist in the engine.
- **React components and Zustand stores:** we use Svelte 5 (ADR-015).
- **Multi-track, transitions, keyframes, AI tools, templates:** out of the MVP scope.
