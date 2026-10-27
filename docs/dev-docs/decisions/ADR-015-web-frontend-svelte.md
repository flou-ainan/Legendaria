# ADR 015 — Web editor front end: Svelte 5 + Vite + TypeScript

**Status:** accepted (owner, 2026-10-27)
**Date:** 2026-10-27
**Related:** ADR-014 (web editor), plan 07, `references/plan07_phase0_spikes.md`

## Context

The web editor (plan 07) needs a UI layer. The spikes showed that the high-frequency work is all imperative and does not depend on a framework:
- the `<video>` element decodes and plays the video;
- JASSUB paints the captions from a worker;
- wavesurfer.js draws the waveform and cue regions.

The framework only handles low-frequency state: the cue list, the selection, the cuts, dialogs and undo.

The owner finds React heavy and wanted something lighter, at most Vue. Copying OpenReel's React stack would bring little, because OpenReel gives us patterns, not code (spike 1.1).

## Decision

- **Svelte 5** (runes: `$state`, `$derived`, `$effect`) with **Vite** and **TypeScript**. Plain Vite with `@sveltejs/vite-plugin-svelte`; no SvelteKit, since the app is one page served by `flosub serve`.
- **State:**
  - one project document (source, kept ranges, cues, style) in a Svelte state module;
  - edits go through small command functions that push undo snapshots.
- **Player rule:**
  - the playhead time is not stored in reactive state at frame rate;
  - a `requestVideoFrameCallback` loop moves the playhead and highlights the current cue directly, or through a single signal that only those elements read.
- **Libraries:** `jassub` (preview), `wavesurfer.js` (waveform, regions, timeline). Anything else needs a reason in the devlog.
- **License of the web UI:** MIT, like the engine.
- **Packaging:** `vite build` output ships inside the `legendaria` wheel. Users need no Node.js; contributors who change the UI do.
- **Build config notes from the spikes:**
  - `worker.format: 'es'`;
  - JASSUB must be tested with a production build, because the dev server's pre-bundling breaks its worker;
  - the server sends COOP/COEP headers.

## Alternatives considered

- **React 19:** familiar to the owner and used by OpenReel. Rejected: its virtual DOM re-renders need care with high-frequency state, it is heavier, and the reuse benefit is small.
- **Vue 3:** mature and close in quality. It was the second choice; Svelte is lighter and closer to plain HTML/JS.
- **SolidJS:** signals with JSX; it has a smaller community.
- **No framework:** the owner's habit in recent projects. Rejected because the editor has enough interlinked UI state (list ↔ timeline ↔ preview ↔ undo) to justify a small reactive layer.

## Consequences

- Contributors need Node.js and npm (or pnpm) to work on `web/`. CI gets a web job: build, type check and tests.
- A PWA later is straightforward (`vite-plugin-pwa`), and the small bundle helps on phones.
- The owner is new to Svelte. Components stay simple, and the code comments point to the Svelte docs where runes are used.
