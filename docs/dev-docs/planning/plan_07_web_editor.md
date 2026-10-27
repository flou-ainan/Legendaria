# Plan 07 — Web editor (replaces the Blender add-on as the main UI)

**Status:** in progress. Phase 0 done (step 29). Phase 1 done: Svelte 5 (ADR-015), project file (ADR-016). Phase 2: first slice done (step 31); next items in "Phase 2 progress" below.
**Date:** 2026-10-26
**Related decisions:** ADR-014 (pivot), ADR-015 (Svelte 5 + Vite + TS), ADR-016 (project file), ADR-012 (`.ass` + libass).
**Supersedes:** plan 05 (local API + `flosub gui`), plan 06 (Blender UX) and the Blender parts of plan 04 §11.

## Why

The Blender add-on works, but for this job it is too much (the owner: "a cannonball to kill an ant"):
- heavy RAM use and desktop freezes (KI-001);
- caption blocks are hard to find and edit (the strips do not show in the default Outliner; text lives in the sidebar);
- the exact preview needs a rendered `.mov`.

The owner wants a lean editor that does only three things:
1. **cut the video** (remove ranges);
2. **edit the subtitles** (text, timing, style);
3. **export**: the video with the subtitles burned in, or SRT / VTT / ASS.

The engine (`flosub`) stays the core: transcription, glossary and review, cues, styles, `.ass`, and FFmpeg burn. The Blender add-on is frozen (ADR-014).

## Research summary (2026-10-26)

| Project | License | Use for us |
|---|---|---|
| [OpenReel Video](https://github.com/Augani/openreel-video) | MIT (but its ffmpeg.wasm core with libass + x264 is GPL-2.0+) | TS + React + Zustand + Vite; MediaBunny/WebCodecs playback. Study and adapt the trim/split logic and timeline patterns (`packages/core/src/editing`, `timeline`, `media`). The timeline UI is tied to its own state, so expect to simplify and rewrite rather than lift it. Do not use its ffmpeg.wasm path. Check the license of any asset before copying it, and keep the MIT notice on copied code. |
| [JASSUB](https://github.com/ThaUnknown/jassub) | MIT wrapper; bundles LGPL parts; libass is ISC | libass in WebAssembly over a `<video>`: an exact `.ass` preview with the same renderer as `flosub burn`, live, with no `.mov`. Threads need COOP/COEP headers (our server sends them). |
| [wavesurfer.js](https://github.com/katspaugh/wavesurfer.js) v8 | BSD-3-Clause | Waveform; the Regions plugin fits a cue track (drag edges, click to time). |
| [Aegisub](https://github.com/Aegisub/Aegisub) | BSD-3 for most files; some MIT/BSD/MPL parts | Ideas only (C++): the timing post-processor (lead-in/out, close small gaps, snap to scene changes), click-to-time on the waveform, the ASS tag model. |
| Burn/cut export | — | On the local Python server with **native FFmpeg** (fast, no WASM memory limits, and no GPL code in our bundle). The browser never encodes. |

## Architecture

```
browser (Svelte 5 + TS + Vite)  ⇄  flosub serve (Python, 127.0.0.1)  →  engine + native FFmpeg
  <video> + JASSUB preview        REST + SSE progress               transcribe / review / ass / render
  timeline: cuts + cue track      serves the built UI + media (HTTP Range)
  waveform (wavesurfer)           COOP/COEP headers
```

- **Project file** `<video>.legendaria.json` (plain JSON, hackable):
  - the source video;
  - the kept ranges (cuts) in source time;
  - the cues (cues JSON v1);
  - the style name.
- **Cues stay in source time.** The UI maps them through the kept ranges, and the export remaps them. A cut never destroys subtitles: undoing it brings them back.
- **Export (`flosub render`):**
  - one FFmpeg pass: `trim`/`concat` of the kept ranges + `ass=` with the remapped cues;
  - SRT / VTT / ASS from the same remap.
- **Packaging:** the built `dist/` ships inside the `legendaria` wheel, so users need no Node.js. Node.js is needed only by contributors who change the UI.
- **UI strings:** a JSON locale in en + pt-BR, the same policy as the add-on.

## Phases

### 0. Study spikes

Results: `docs/dev-docs/references/plan07_phase0_spikes.md` (step 29).

1. **OpenReel:**
   - clone it outside the repo;
   - map `editing`, `timeline`, `playback` and `media`;
   - try to extract trim/split and a reduced timeline;
   - list what can be lifted and what gets rewritten.
2. **JASSUB:**
   - load our `pop` `.ass` over the owner's clip;
   - compare frames with `flosub burn` (the pixel diff as in step 23);
   - check `\t`, alpha and seek precision.
3. **wavesurfer.js** Regions as the cue track: drag edges, split, performance with ~500 cues.
4. **FFmpeg** cut + burn in one command, plus the time remap, with pytest.

### 1. Decisions

- **ADR-015:** front-end stack and reuse policy. The proposal is TS + React + Vite, to match OpenReel so code can be reused; this reverses plan 05's "no build step". It also covers the server library (stdlib vs a small dependency).
- **ADR-016:** project file format; cuts kept in source time. This resolves plan 04 §11.5 (storage format): a JSON project with cues, and `.ass` as an export.

### 2. MVP build

1. `flosub serve`: an API for media, transcribe (SSE progress), review, glossary, project load/save, and render/export.
2. A web shell with an open/transcribe screen and progress.
3. A player with the JASSUB preview.
4. A cue list editor: text, times, split/merge, and review suggestions.
5. A timeline: cut ranges, a cue track and a waveform, with snapping.
6. An export dialog: burned MP4, SRT, VTT or ASS.
7. pt-BR.

#### Phase 2 progress

| # | Item | Status |
|---|---|---|
| 1 | `flosub serve`: media (Range), state, project load/save, transcribe and export jobs (SSE), preview `.ass`, font | done (step 31); review/glossary routes still to do |
| 2 | Open/transcribe screen with progress | done (step 31) |
| 3 | Player with the JASSUB preview, live update after each edit | done (step 31) |
| 4 | Cue list: text, times, split, merge, delete, add | done (step 31); review suggestions still to do |
| 5 | Timeline: cuts + cue strip | basic strip done (step 31). To do: wavesurfer waveform with server peaks, draggable cue edges, snapping (pixels + word boundaries), zoom at cursor, follow playhead |
| 6 | Export: burned MP4, SRT, VTT, ASS | done (step 31) |
| 7 | pt-BR | done (step 31) |
| — | Undo/redo with grouping, autosave, shortcut table (JSON) | done (step 31) |
| — | Tests: engine pytest (remap, project, server, real cut + burn), Vitest (timeline) | done (step 31). Playwright smoke test in CI: to do (it ran locally) |

**Next slice (step 32 proposal), after the owner's manual test:**
- waveform + draggable cues + snapping + zoom — tier: standard, effort: medium — the spikes (1.3) and the OpenReel dissection already define the approach;
- review/glossary suggestions in the cue list — tier: standard, effort: medium — reuses `cli.run_review`, needs a small refactor;
- Playwright smoke in CI — tier: standard, effort: low — the local script from step 31 exists.

### 3. Freeze Blender

- The README and the docs say the add-on is frozen.
- CI keeps a single Blender smoke job, so the add-on does not silently break.

## Code (MVP)

- **New:**
  - `engine/legendaria_engine/server.py`;
  - `engine/legendaria_engine/project.py` (kept ranges, remap);
  - `render()` in `media.py`;
  - `web/` (Vite app).
- **Reused:**
  - `ass.to_ass`, `media.probe` / `run_ffmpeg`, `CueList.from_dict`, `formats`;
  - the review and glossary logic behind `cli.cmd_review` and `cmd_glossary`, refactored into functions that the CLI and the server both call.

## Definition of done (MVP)

- [ ] The owner opens a video in the browser, transcribes it, fixes the text, cuts out a range, and exports a burned MP4 and an SRT.
- [ ] The JASSUB preview matches the burned frame (pixel diff as in step 23).
- [ ] Engine pytest covers the remap and the project file, plus a real FFmpeg cut + burn in CI.
- [ ] Web: Vitest for the timeline and remap logic; a Playwright smoke test (open → transcribe fixture → edit → export SRT).
- [x] Docs: ADR-015/016, `PROJECT.md`, a devlog step for each phase, en + pt-BR UI.

## Owner answers (2026-10-26)

- **Framework:** the owner finds React heavy and prefers something lighter (at most Vue). React only if copying OpenReel's stack is clearly best. The spikes showed it is not (OpenReel gives patterns, not code), so the recommendation is Svelte 5 + Vite + TS, with Vue 3 second. **Decided 2026-10-27: Svelte 5** (ADR-015).
- **Backend:** export and cuts always call the local server. A standalone mobile PWA without a backend is out of scope for now.
- **MVP cuts:** lean. Remove ranges only.

## Later (after the MVP)

- Reorder and duplicate ranges, multiple source clips.
- Aegisub-style timing helpers: snap to scene changes, close small gaps, lead-in/out.
- Canvas-drawn cue track for videos with thousands of cues.
- A standalone PWA (whisper.cpp/WASM), and the web editor on a phone through the desktop server.
- Font picker and bundled free fonts (libass in the browser only sees the fonts we serve).

## Open questions for the owner

None right now. Still pending from earlier: import `.ass`/`.srt` + `flosub align --srt` (plan 04 §11.3, item 4).
