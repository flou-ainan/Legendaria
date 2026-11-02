# Plan 07, phase 0 — study spikes (results)

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

The spikes ran outside the repository, because they use the owner's media: `../legendaria-spikes/` next to the repo, on the owner's machine. Nothing in that folder is committed.

The test clip is the owner's crochet video: the first 20 s, 1920×1080, 24 fps. The `pop` style was used throughout.

## 1.1 OpenReel Video: what is useful for us

- **Size:** ~460,000 lines of TypeScript (pnpm monorepo, React 19 + Zustand 4 + immer, MediaBunny/WebCodecs). For comparison, the web timeline alone is `Timeline.tsx` at 1,753 lines plus `ClipComponent.tsx` at 1,025.
- **Why its engine does not fit us:**
  - OpenReel decodes frames itself (WebCodecs → canvas/WebGPU) because it composites many tracks, effects and transitions;
  - we have **one source video**, so a plain `<video>` element plays it, and JASSUB draws the captions on top. Its whole decode / frame-cache / render pipeline is not needed.
- **What could be lifted:**

| Module | Lines | Verdict |
|---|---|---|
| `playback/master-timeline-clock.ts` | 268 | Not needed: with one `<video>`, the video is the clock (`requestVideoFrameCallback`). |
| `media/waveform-generator.ts`, `waveform-renderer.ts` | 811 | Replaced by wavesurfer.js plus server-side peaks (1.3). |
| `timeline/clip-manager.ts` (split / trim / snap, undo actions) | 723 | **Ideas worth reading** (snap threshold, action history); the code depends on their Timeline/Action types. |
| `text/subtitle-engine.ts` | 649 | The engine already has SRT/VTT/ASS. |
| `export/*` (WebCodecs encode) | 2,868 | Not used: export runs on the server with native FFmpeg. |
| Web timeline UI (React) | 1,700+ | Not reusable as is; tied to their store. Useful as a UX reference (layout, shortcuts). |

- **Conclusion:** the useful part of OpenReel is patterns, not code. Copying its stack brings little benefit, so the framework choice is free (see "Front-end framework" below). If any file is copied, keep its MIT notice.

## 1.2 JASSUB (libass in WebAssembly) as the exact preview

- **Setup:**
  - `jassub` 2.5.23 with Vite 6;
  - a production build is needed (`vite build` + `vite preview`), with `worker.format: 'es'`;
  - the dev server's dependency pre-bundling breaks the JASSUB worker. Plan 07 serves the built UI anyway.
- COOP/COEP headers on the server → `crossOriginIsolated`, so the worker uses threads.
- Ready in **170–530 ms**. The WASM is 2.1 MB (0.9 MB gzipped).
- **Fonts:** libass in the browser cannot see system fonts unless we pass them. Here `Arial_Bold.ttf` was given via `availableFonts`. The server will have to serve the font files a style uses (or bundle free fonts).
- **Comparison with FFmpeg's `ass` filter**, frame by frame on black (`compare.py`, frames 12–16 = pop animation, 42, 100, 250, 400):
  - 9.4–12.8 mean difference on caption pixels (0–255), and 23.6 on frame 13, mid-pop;
  - the differences are 1-pixel anti-aliasing edges; the side-by-side crops look identical;
  - scale animations (`\t`), position and colors match.
- **Caveat:** the first render after loading is empty while the font loads, so the UI should wait for the first paint.

## 1.3 wavesurfer.js v8 as the cue track

wavesurfer.js was bound to the `<video>` (`media` option) with one Region per cue. Results from headless Chrome:

| Case | Ready | Add regions | JS heap | 5 zoom steps | 20 seeks |
|---|---|---|---|---|---|
| Clip 20 s, 43 real cues | 35 ms | 7 ms | 2 MB | 118 ms | 332 ms |
| 10 min, 500 cues, browser decodes the audio | 1,241 ms | 50 ms | 27 MB | 115 ms | 337 ms |
| 10 min, 500 cues, **peaks from the server** | **53 ms** | 36 ms | **9 MB** | 74 ms | 327 ms |

- **Server peaks:** FFmpeg → 8 kHz mono → max per 10 ms bin (`peaks.py`). 10 min takes 1.2 s and gives a 400 KB JSON. For long videos this avoids decoding the whole audio in the browser (RAM). **Decision input: peaks come from the server.**
- **Editing:** a mouse drag of a region edge updates the cue (`region-updated`), and split at the playhead works.
- **Limits:** regions are DOM elements. 500 is smooth; for thousands, render only the visible window, or draw cues on a canvas later.

## 1.4 Cut + burn in one FFmpeg pass

- **Remap:** `remap(cues, keep)` moves the cues onto the output timeline:
  - cues inside a removed range disappear;
  - cues across a cut are clipped;
  - slivers under 80 ms are dropped.
  - Four pytest cases pass.
- **One command:** `trim`/`atrim` per kept range → `concat` → `ass=subs.ass`, H.264 CRF 18 + AAC.
- **Result:**
  - the test kept 0–4, 7–12.5 and 15–20 s;
  - the output is 14.5 s as expected, rendered in 8.0 s;
  - 43 → 31 cues;
  - SRT and VTT were written from the same remapped cues.
- **Sync check:** the frames right after each cut show the same caption and the same mouth position as the source at the matching time (`sync_check.png`).

## Front-end framework (owner question 2.1)

**What the spikes show:** the heavy, high-frequency parts are imperative and framework-independent:
- the `<video>` decodes;
- JASSUB paints in a worker;
- wavesurfer draws on its own canvas.

The UI framework only manages low-frequency state: the cue list, the selection, the cuts, dialogs and undo.

**The player rule, whatever the framework:**
- the playhead time never goes through the reactive store at 60 fps;
- a `requestVideoFrameCallback` loop moves the playhead and highlights the current cue directly (or through one fine-grained signal);
- the project document (cues + cuts) is the only app state, with undo as a stack of snapshots or patches.

| Option | Runtime (gzip, approx.) | Reactivity | Fit |
|---|---|---|---|
| React 19 (OpenReel's) | ~45 KB | Virtual DOM; whole-subtree re-renders unless memoized | Owner knows it; reuse benefit is small (1.1). |
| Vue 3 | ~35 KB | Proxy-based, component-level updates | Mature, SFCs, Pinia; easy for contributors. |
| **Svelte 5** | ~5–15 KB (compiled) | Signals (runes `$state`, `$derived`), fine-grained, no virtual DOM | Closest to plain HTML/JS, the smallest output, Vite plugin; no SvelteKit needed. |
| SolidJS | ~7 KB | Signals, JSX | React-like syntax with fine-grained updates; smaller community. |

**Recommendation:** Svelte 5 + Vite + TypeScript, with Vue 3 as a close second. This is the input for ADR-015; the owner decides.
