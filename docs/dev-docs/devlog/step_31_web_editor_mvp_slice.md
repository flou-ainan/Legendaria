# Step 31 — Web editor: project file (ADR-016), `flosub serve`, first Svelte slice

**Date:** 2026-10-27
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_07_web_editor.md (phases 1 and 2)

## What was done

- **ADR-016, project file:** `<video>.legendaria.json`, plain JSON with `format`/`version`, the source, its duration, the style, the kept ranges and the cues, all in source time. `.ass`/SRT/VTT are exports. JSON Schema in `engine/schemas/project.schema.json`. This settles plan 04 §11.5 (own JSON vs `.ass` vs extended `.ass`).
- **Engine:**
  - `project.py`: `Project` (validate, normalize, atomic save), `normalize`, `remove_range`, `remap`, `output_duration`, `project_path`. The remap is the spike 1.4 code, now with tests.
  - `media.render()` + `cut_graph()`: one FFmpeg pass that trims the kept ranges, concatenates them and burns the remapped `.ass`. Videos without audio work. `probe()` now reports `has_audio`. New config key `burn.render_audio_args` (AAC 192k by default; the audio must be re-encoded when cut).
  - `server.py` + `flosub serve VIDEO`: standard library only (`ThreadingHTTPServer`). Serves the built app, the video with HTTP Range, the project (GET via state, PUT to save), the preview `.ass` (source time), the style's font file (fontconfig), and transcribe/export jobs with Server-Sent Events. Listens on 127.0.0.1 and answers 403 to a non-local Host or Origin. Transcription runs `flosub transcribe` as a child process, because the CUDA setup may re-exec the process.
- **Web app (`web/`, Svelte 5 + Vite 8 + TypeScript 6):**
  - transcribe screen (model, language, style, progress);
  - player: `<video>` + JASSUB, cut parts skipped during playback, playhead and current cue updated from a `requestVideoFrameCallback` loop (no reactive state at frame rate, ADR-015);
  - a strip with cues, cuts and the in/out mark; click to seek;
  - cut by marking in/out (I, O, X), a cuts list with "restore";
  - cue list: text, start/end, split at the playhead (by words when available), merge with next, delete, add at playhead; cues inside a cut are dimmed;
  - undo/redo with snapshot history and grouping of rapid edits on the same field; autosave 400 ms after the last edit, then the preview `.ass` is refreshed in JASSUB;
  - export MP4 / SRT / VTT / ASS with progress;
  - en + pt-BR strings; keyboard shortcuts in an editable `lib/shortcuts.json`.
- **Packaging and CI:** `vite build` writes into `engine/legendaria_engine/web/` (gitignored); hatch `artifacts` puts it in the wheel; `release.yml` builds the web app before the wheel. CI gets a `web` job (type check, Vitest, build), and the aggregate `ci` check requires it.
- **AGENTS.md:** new rule "Recommending the model for the next task": vendor-neutral tiers (standard / top) and effort levels (low / medium / high), ending each task with one line for the next one. Asked by the owner.

## Why

ADR-016 and the MVP build were the agreed next step (owner: "Sim continue"). The slice goes end to end (open → edit → cut → export) so the owner can test the editor before the timeline work.

## Problems found and fixed

- **Tiny cuts:** a cut shorter than 10 ms left a gap that the cuts list did not show. Found by the random property test. Cuts under `MIN_RANGE` are now ignored, in Python and TypeScript.
- **JASSUB fonts:** libass looks fonts up by lowercase family name (`arial`), so the served font is registered under the style's family. It is also passed in `fonts`, so it is loaded up front; otherwise the first frame drawn before any playback had no font and stayed empty.
- **Paused seeks:** the browser may not report a new frame after a seek while paused. The player calls `manualRender` on `seeked` and after each preview refresh.
- `svelte-check` does not support TypeScript 7 alone yet; TypeScript is pinned to 6.

## Files touched

- New:
  - `engine/legendaria_engine/project.py`, `engine/legendaria_engine/server.py`;
  - `engine/schemas/project.schema.json`;
  - `engine/tests/test_project.py`, `engine/tests/test_server.py`;
  - `web/` (package files, `vite.config.ts`, `tsconfig.json`, `svelte.config.js`, `index.html`, `src/`);
  - `docs/dev-docs/decisions/ADR-016-project-file.md`, this step.
- Changed: `engine/legendaria_engine/media.py`, `cli.py`, `defaults/config.json`, `engine/schemas/config.schema.json`, `engine/pyproject.toml`, `.gitignore`, `.github/workflows/ci.yml`, `release.yml`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/PROJECT.md`, `docs/dev-docs/planning/plan_07_web_editor.md`, `docs/dev-docs/chat-context.md`.

## How it was tested

- Engine: `uv run --extra test pytest`: 120 passed, including a real FFmpeg cut + burn (6 s source, 1–3 s removed → 4.0 s output with audio) and the server routes over HTTP.
- Web: `npm run check` (0 errors, 0 warnings), `npm test` (5 Vitest tests, including a 200-case random property test), `npm run build`.
- End to end with Playwright (headless Chromium, run locally with a scratch script, not yet in CI), on a synthetic 10 s WebM clip (Playwright's Chromium has no H.264) and a project with 10 cues:
  - the page is cross-origin isolated, with no console errors;
  - I / O / X cut 3–6 s; editing a cue's text autosaves; the saved project has `keep [[0,3],[6,10]]`;
  - two Ctrl+Z restore the cut and the text; redo brings them back;
  - playing from 2.8 s jumps over the cut (6.36 s after 0.7 s);
  - export SRT (timing shifted by the cut) and MP4 (7.0 s);
  - screenshots show the pop look from JASSUB on the first paused seek, and a text edit appears in the preview without reloading.
- `uv build --wheel` includes the 9 web files. `pre-commit run --all-files` passes.
- Real transcription through the server (`POST /api/transcribe`, model `tiny`, the owner's 20 s test clip, outside the repo): events streamed over SSE (glossary log, start on CUDA, progress, done), and the project was created with 41 cues and nothing cut.
- Not tested yet: the transcribe screen clicked in a real browser, Windows/macOS fonts (`fc-match` is Linux-first; without it, JASSUB uses its bundled font, so the preview font can differ from the export).

## Pending / next steps

- **Owner's manual test:** `flosub serve <video>` on a real clip.
- Next slice (plan 07, "Phase 2 progress"): waveform with server peaks and draggable cue edges, snapping (pixels + word boundaries), zoom at cursor; review/glossary suggestions in the cue list; the Playwright smoke test in CI.
- Font lookup on Windows/macOS (no fontconfig): later, together with the font picker (plan 07, "Later").
