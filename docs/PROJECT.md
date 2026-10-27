# Project Map — Legendária

> A condensed map of the project, so agents and people can find what they need without rereading the code.
> **Update this file with every change to the project** (files, functions, stack, structure). Conventions: `docs/dev-docs/README.md`.

**Last updated:** 2026-10-27 — step 33 (web editor: owner's first round of corrections: open from the browser, dropdowns, glossary tools, live snap, new layout).

---

## 1. Overview

**Legendária** ("free subtitles, CapCut style") is a free, open-source automatic subtitle creator, inspired by CapCut's auto captions. Names (ADR-009): product **Legendária**; repository, Python package and add-on id `legendaria`; CLI command `flosub`.

What it does:

- Transcribes the audio locally on the GPU, with per-word timings.
- Turns the result into **editable text strips in Blender's Video Sequence Editor**.
- Exports SRT/VTT, or renders the video with the subtitles burned in.

Goals: a "next → next → finish" install for end users; a hackable setup driven by JSON configs; friendly to contributors; Linux, macOS and Windows 10+; UI and user docs in English and pt-BR (open to more languages).

**Current state:** the engine (`flosub`, on PyPI as `legendaria`) and the Blender add-on core work end to end: select a video in the VSE, pick a model (auto-download), generate CapCut-style caption strips in the background, confirm before replacing, re-apply a style, export SRT/VTT, English/Portuguese UI. "Install engine" sets everything up from Blender (2b); "Regenerate range" redoes only the preview range or the selected captions (2c). The default style is "one word, pop" (yellow). Accuracy (plan 03): a glossary library steers Whisper and drives a review that suggests corrections; in Blender the panel picks the active glossary (new / import / export / edit), adds terms from a caption or a suggestion, reviews and applies ticked corrections in place. An LLM reviewer exists but is experimental and off by default. Styled output: `.ass` export with the pop look, `flosub burn` (FFmpeg) and, in Blender, an "Exact preview" overlay rendered by libass that the normal render burns in. **Direction change (ADR-014):** the Blender add-on is frozen; the main UI becomes a local web editor (plan 07). The MVP works (steps 31–33): `flosub serve` opens it in the browser, which asks for a video (file browser or drag and drop); it transcribes, edits the subtitles on a timeline with a live libass preview (JASSUB), cuts out ranges, undoes, manages the glossary, and exports a burned MP4 or SRT / VTT / ASS. The document is `<video>.legendaria.json` (ADR-016). Plans: `dev-docs/planning/`.

## 2. Architecture

Two independent parts that talk through a JSON file and JSON-lines progress events:

```
[video strip in Blender's VSE]
        │  add-on launches the engine (subprocess, own venv)
        ▼
engine/ (`flosub`) ── faster-whisper (GPU → CPU fallback) ──► transcript JSON v1 (segments + words)
        │                                      │  progress: JSON lines on stdout
        ▼                                      ▼
   SRT / VTT (CLI)            add-on creates editable text strips
                                        │
                                        ├──► Export SRT / VTT (from the edited strips)
                                        └──► Blender render with burned-in subtitles
```

- **Engine (`engine/`, MIT):** a standalone Python package with its own venv and the `flosub` command (transcribe / export / models / config). It works on its own as a CLI.
- **Add-on (`blender_addon/legendaria/`, GPL-3.0-or-later):** a Blender 4.2+ extension with a sidebar UI. It is translated through `bpy.app.translations` with `locales/*.json`.
- **Config:** shipped JSON defaults, overridden by a per-OS user JSON file, overridden in turn by CLI flags or UI values (ADR-006).

## 3. Technologies / stack

| Layer | Technology |
|---|---|
| Transcription | faster-whisper 1.2 (CTranslate2 4.6), fp16 on GPU / int8 on CPU, default model `small` |
| GPU acceleration | CUDA 12 via the optional `cuda` extra (`nvidia-cublas-cu12` + `nvidia-cudnn-cu12` 9), no PyTorch; Linux and Windows. `cuda_libs.py` makes them loadable |
| Media decoding | PyAV (bundled with faster-whisper) / FFmpeg |
| Styled subtitles | `.ass` written by the engine, rendered by libass through FFmpeg's `ass` filter (burn-in and transparent qtrle overlay). FFmpeg is optional: only `burn`, `overlay` and the size probe for `.ass` need it (ADR-012) |
| Editor | **Web editor (in progress, plan 07):** Svelte 5 + Vite + TypeScript, served locally by `flosub serve`; JASSUB (libass in WASM) for the exact preview, wavesurfer.js for waveform and cue regions; cuts and burn-in on the server with native FFmpeg (ADR-014, ADR-015). **Frozen:** Blender 4.2+ VSE add-on (`bpy`, extension format) |
| Language | Python 3.10+ (engine; dev venv pinned to 3.11 via `uv` and `engine/.python-version`) / Blender's bundled Python (add-on) |
| Config | JSON + JSON Schema, `platformdirs` for per-OS paths |
| i18n | `bpy.app.translations` + `locales/<lang>.json` (en source, pt_BR maintained) |
| Tests / quality | pytest + jsonschema (engine), ruff + pre-commit, GitHub Actions on Linux/macOS/Windows |
| Reference hardware | RTX 2070 Super 8 GB, Linux Mint 22 |
| Targets | Linux, macOS, Windows 10+ |

## 4. Technical decisions

| ADR | Decision | Status |
|---|---|---|
| [001](dev-docs/decisions/ADR-001-faster-whisper.md) | faster-whisper as the engine (Ollama cannot run Whisper) | accepted |
| [002](dev-docs/decisions/ADR-002-blender-vse-editor.md) | Blender VSE (4.2+) as the interactive editor | superseded (ADR-014) |
| [003](dev-docs/decisions/ADR-003-engine-external-process.md) | Engine as an external process in its own venv, JSON contract | accepted |
| [004](dev-docs/decisions/ADR-004-dual-licensing.md) | Engine MIT, add-on GPL-3.0-or-later | accepted |
| [005](dev-docs/decisions/ADR-005-language-policy.md) | English dev content; user content in en + pt_BR, open to more | accepted |
| [006](dev-docs/decisions/ADR-006-json-configuration.md) | Layered JSON config files with JSON Schema | accepted |
| [007](dev-docs/decisions/ADR-007-cross-platform.md) | Linux, macOS, Windows 10+ | accepted |
| [008](dev-docs/decisions/ADR-008-contribution-workflow.md) | Branch + PR, Conventional Commits, SemVer, CI on 3 OSes | accepted |
| [009](dev-docs/decisions/ADR-009-project-name.md) | Name: Legendária (`legendaria`), CLI `flosub` | accepted |
| [010](dev-docs/decisions/ADR-010-review-pipeline.md) | Glossary in 3 layers + LLM reviewer (OpenAI-compatible, suggestions), device profiles | accepted |
| [011](dev-docs/decisions/ADR-011-modular-architecture.md) | Engine core → CLI/HTTP API → clients (Blender, web GUI, Kdenlive later) | accepted |
| [012](dev-docs/decisions/ADR-012-ass-styled-format.md) | `.ass` as styled format: one preset → `.ass` (libass overlay/burn) and Blender strips | accepted (MVP subset, step 23) |
| [013](dev-docs/decisions/ADR-013-blender-5-2-minimum.md) | Blender 5.2 LTS is the minimum (4.x support dropped; implementation after the manual test) | suspended (ADR-014) |
| [014](dev-docs/decisions/ADR-014-web-editor-blender-frozen.md) | Web editor (`flosub serve`) becomes the main UI; Blender add-on frozen | accepted |
| [015](dev-docs/decisions/ADR-015-web-frontend-svelte.md) | Web editor front end: Svelte 5 + Vite + TypeScript (MIT) | accepted |
| [016](dev-docs/decisions/ADR-016-project-file.md) | Project file `<video>.legendaria.json`: own JSON, cuts as kept ranges, cues in source time; `.ass`/SRT/VTT are exports | accepted |
| [017](dev-docs/decisions/ADR-017-opening-files-in-the-browser.md) | Opening a video from the browser: a server-side file browser (opens in place) and drag-and-drop upload (stores a copy) | accepted |
| [018](dev-docs/decisions/ADR-018-local-recovery-and-relink.md) | Local recovery copy (IndexedDB) and relinking a moved video | accepted |

## 5. Folder structure

```
Legendaria/
├── AGENTS.md                # instructions for any AI agent (and humans)
├── CLAUDE.md                # points to AGENTS.md
├── README.md                # user-facing, English
├── README.pt-BR.md          # user-facing, Brazilian Portuguese
├── CONTRIBUTING.md          # setup, workflow, style, adding a language, licensing
├── CODE_OF_CONDUCT.md       # Contributor Covenant 2.0
├── SECURITY.md              # private vulnerability reporting
├── CHANGELOG.md             # Keep a Changelog, SemVer
├── LICENSE                  # MIT
├── ruff.toml                # lint/format config for all Python
├── .pre-commit-config.yaml  # ruff + basic file checks (run in CI too)
├── .editorconfig / .gitattributes   # LF endings, indentation
├── .gitignore
├── engine/                  # MIT — transcription engine, Python package "legendaria", CLI `flosub`
│   ├── pyproject.toml       # deps; extras: cuda (NVIDIA libs), test (pytest, jsonschema); script flosub
│   ├── uv.lock / .python-version (3.11)
│   ├── README.md, LICENSE
│   ├── legendaria_engine/   # the package (see file map); review/ = glossary, hotwords, fix rules, suggestions (plan 03)
│   │   └── defaults/        # config.json (engine defaults), models.json (model catalog)
│   ├── schemas/             # JSON Schemas: config, models, transcript (editor autocomplete)
│   └── tests/               # pytest suite (no GPU or network needed)
├── blender_addon/           # GPL-3.0-or-later — Blender 4.2+ extension
│   ├── legendaria/          # the extension (see file map): manifest, LICENSE, *.py, presets/, locales/
│   └── tests/               # pure-Python tests + blender_smoke.py (inside Blender) + ui_walkthrough.py (GUI)
├── web/                     # MIT — web editor (Svelte 5 + Vite + TS); `npm run build` writes into engine/legendaria_engine/web/ (gitignored, shipped in the wheel)
│   ├── src/                 # App.svelte, components/, lib/ (state, API, timeline math), locales/ (en, pt-BR)
│   └── package.json / vite.config.ts / tsconfig.json
├── tools/
│   └── project_map.py       # prints the "File map" entries below from the source
├── .github/
│   ├── workflows/ci.yml     # pre-commit, engine + add-on tests on Linux/macOS/Windows; add-on smoke test inside Blender 4.2.23 and 5.2.3; web job (type check, Vitest, build); aggregate `ci` check
│   ├── workflows/release.yml  # on tag vX.Y.Z: test, build the web editor, build and publish the engine to PyPI (Trusted Publishing, env `pypi`)
│   ├── ISSUE_TEMPLATE/      # bug, feature, translation forms + links to Discussions / security
│   └── pull_request_template.md
├── assets/
│   └── brand/           # brand kit: glowing key art (banner/hero/cover per language), flat symbol/icons/lockups, PNGs, favicon
└── docs/
    ├── PROJECT.md           # this file
    └── dev-docs/
        ├── README.md        # documentation conventions
        ├── chat-context.md  # condensed owner ↔ agent conversation + last two full replies (hand-off)
        ├── planning/        # plans (before implementing)
        ├── devlog/          # executed steps
        ├── decisions/       # ADRs
        ├── known-issues.md  # problems seen in real use, with evidence and how to investigate
        └── references/      # origin_brainstorm.md, ass_brainstorm.md, plan07_phase0_spikes.md, openreel_dissection.md
```

Build the add-on package: `blender --command extension build --source-dir blender_addon/legendaria --output-dir dist` (gives `legendaria-<version>.zip`, installed with Edit → Preferences → Get Extensions → Install from Disk).

User files at runtime (per OS, via `platformdirs`; overridable with `LEGENDARIA_CONFIG_DIR` / `LEGENDARIA_DATA_DIR`):
- data dir `engine/` (only when installed from Blender): `uv/`, `python/` (uv-managed 3.11), `venv/` (flosub). Deleting it uninstalls.
- config dir (`~/.config/legendaria` on Linux): `config.json`, `models.json`, `providers.json`, `review_prompt.txt` (user overrides), `glossaries/<name>.txt` (glossary library), `presets/` (add-on style overrides)
- data dir (`~/.local/share/legendaria` on Linux): `models/<name>/` (downloaded CTranslate2 models)

## 6. File map

Generated with `python3 tools/project_map.py <files>` and then reviewed. Regenerate it whenever code changes.

**Data files:**
- `engine/legendaria_engine/defaults/providers.json` (LLM provider presets) and `review_prompt.txt` (reviewer prompt template).
- `engine/legendaria_engine/defaults/config.json`: engine defaults (`review`: mode suggest/auto, profile, glossary_bias, fuzzy_threshold 0.82, low_confidence 0.5, `llm` {enabled false (experimental), provider ollama, model, batch/context lines, max_change_ratio, unload_after}; model `small`, language `auto`, device `auto`, compute types, beam size, VAD, word timestamps, default `style`, cue `styles` (`pop`: one word at a time, two when the first has ≤ 3 letters, glued pieces like "-vindas" kept, gaps ≤ 0.35 s filled — the MVP default in Blender; `captions`: up to 4 words / 22 chars / 2.2 s; `subtitles`: film-style, up to 84 chars / 6 s, 2 lines of 42), output formats, UI language list; each style has an `ass` look block: font, size at 1080 px on the short side, RGBA colors, outline, shadow, box, position, uppercase, `animation` none/pop; `ffmpeg` path and `burn` encoder arguments, incl. `render_audio_args` for cut exports).
- `engine/legendaria_engine/defaults/models.json`: model catalog (tiny, base, small, medium, large-v3, large-v3-turbo) with HF repo, size, VRAM, notes.
- `engine/schemas/*.schema.json`: JSON Schemas for config (incl. styles), models, transcript v1, cues v1 and project v1 (ADR-016).
- `engine/tests/`: `conftest.py` (isolated dirs, sample transcript), `test_cues.py` (chunking rules), `test_formats.py`, `test_schema.py`, `test_config.py`, `test_cli.py`, `test_transcriber.py` (GPU→CPU fallback with a fake run), `test_glossary.py`, `test_fix_rules.py`, `test_llm_review.py` (fake OpenAI-compatible server), `test_glossary_library.py`, `test_ass.py` (the `.ass` writer, export from edited cues, burn and overlay when FFmpeg is on PATH), `test_project.py` (kept ranges, remap incl. a random property test, project file + schema, a real cut + burn), `test_server.py` (`flosub serve` routes: state, Range, local-only guard, save, export SRT, preview `.ass`, peaks, review; starting without a video, browse, open/upload, glossary add/import/export). 127 tests, no network.
- `engine/legendaria_engine/defaults/languages.json`: language codes for the transcribe form (a user copy in the config dir wins).

**Glossary and review (plan 03):** glossary files are plain text (`Term` or `wrong -> right`). Sources, merged in order: the **active glossary of the library** (`<config dir>/glossaries/<name>.txt`, config `review.glossary`, `flosub glossary list|new|use|import|export|delete`; an old `glossary.txt` migrates to "default"), the project file `legendaria-glossary.txt` next to the media or transcript, and `--glossary FILE|NAME`. `transcribe` passes the terms to Whisper as `hotwords` (layer 1). `flosub review FILE.json` (or `transcribe --review`) finds explicit fixes and fuzzy matches of uncertain words (layer 2) and writes `<name>.review.json` (mode `suggest`) or applies them (`auto`). `flosub review apply FILE.review.json --ids …|--all [--format srt]` applies the chosen ones, re-timing the words. `flosub glossary path|show|add` is the base of every UI's "Add to glossary". **Layer 3 (stage 3b, EXPERIMENTAL, off by default):** `review --llm` sends batches (with context, uncertain words marked `[[…]]`) to any OpenAI-compatible server (`defaults/providers.json`: ollama, lmstudio, llamacpp, openai, gemini, anthropic, openrouter; keys from env vars) using the editable prompt `defaults/review_prompt.txt` (user copy in the config dir wins); the model returns only changed lines, which are diffed word by word and kept only if the guard allows (accent-only fixes, or similar-sounding changes of uncertain words / to glossary terms; never deletions). `flosub llm check|providers`. Config `review.profile` (light/standard = no LLM) and `review.llm.enabled: auto` degrade gracefully when no server answers.

**Range regeneration:** `flosub transcribe media --clip START,END --update saved.json` transcribes only that range and merges it into the saved transcript word by word (`Transcript.merged_with`), so nothing is duplicated or lost at the boundaries.

**Outputs of `flosub transcribe` / `export`:** `<name>.json` (transcript v1: segments + word timings, the source of truth), `<name>.cues.json` (cues v1 in one style), `<name>.srt` / `.vtt` / `.ass` (from the cues; `.ass` uses the style's look, on the video's size or `--size`). `export` re-chunks a saved transcript in any style without transcribing again, or takes an edited cues JSON as is (how Blender exports its strips).

**Styled output (plan 04 §10):** `flosub burn VIDEO [--subs FILE] [--style]` writes `VIDEO.subtitled.mp4` with the subtitles drawn in. `flosub overlay SUBS --size --fps --duration` writes the subtitles alone to a transparent `.mov` (Blender's exact preview). Both take a transcript, a cues JSON or an `.ass`, report `progress`, and find FFmpeg through config `ffmpeg` or PATH.

**Progress event protocol** (stdout, one JSON object per line, `--progress json`):
- `start`: model, device, compute_type, language, duration.
- `progress`: `t`, `total` (in seconds).
- `model_download`: downloaded / total bytes, or `finished`.
- `log`, `warning`, `error`: carry `message`.
- `done`: `outputs` plus counts.

A `warning` followed by a new `start` means the run restarted on the CPU.

**Web editor (`web/`, plan 07):** `flosub serve [VIDEO] [--port 8765] [--no-browser]` serves the built app on 127.0.0.1 with COOP/COEP headers; without a video the browser asks for one. API: `GET /api/state` (video or null, probe, project, font family, and the options for the transcribe form: models with `installed`, languages, styles, defaults), `GET /api/browse?path=` (folders and media files of the computer), `POST /api/open` {path} and `POST /api/upload?name=` (a dropped file is stored in `<data dir>/uploads/`), `GET /api/glossary` and `POST /api/glossary/add|import|use`, `GET /api/glossary/export?name=` (the glossary library; they work without a video, the other routes answer 409 then), `GET /api/media` (HTTP Range), `GET /api/font` (fontconfig match of the style's font, so JASSUB draws like FFmpeg), `GET /api/preview.ass` (project cues in source time), `GET /api/peaks` (waveform peaks, 100 per second, streamed from FFmpeg once per session), `GET /api/review` (glossary suggestions for the saved cues: the engine's layer 2, no AI), `PUT /api/project` (validated, normalized, saved atomically), `POST /api/transcribe` and `POST /api/export` {format mp4|srt|vtt|ass} start a job; `GET /api/jobs/<id>/events` streams its events (SSE, same events as `--progress json`). Requests with a non-local Host or Origin get 403. Transcription runs `flosub transcribe` in a child process. Exports go next to the video as `<stem>.edited.<ext>`. Dev: `npm run dev` in `web/` proxies `/api` to a running `flosub serve … --no-browser`.

### web/src (Svelte 5 + TypeScript, 1617 lines + tests)

Layout (step 33): a header, the video with a tool row under it (play, in, out, cut, split, snap magnet, undo, redo), an inspector for the selected block, and the timeline. Everything happens there; the side drawer (subtitles list, glossary, cuts, export) is optional and closed by default. On narrow screens the drawer is a bottom sheet.

| File | Lines | What it does |
|---|---|---|
| `main.ts` | 5 | Mounts `App.svelte`. `app.css`: theme tokens, base controls, and the style of wavesurfer's cue text (it draws in a shadow root). |
| `App.svelte` | 128 | Loads `/api/state`; Welcome when no video is open, Transcribe until a project exists, then the editor layout and the header (menu, logo, save status, panel buttons, Export); Save now and Download a copy. |
| `components/Welcome.svelte` | 141 | Start screen: drop a video on the page (uploaded) or "Choose a file…" (opened in place); "Continue where you left off" from the browser's recovery copy, and relinking a moved video (same duration ±0.5 s and screen proportion ±1 %). |
| `components/Menu.svelte` | 65 | File menu (open video/project, close, save, download a copy, export), panels on narrow screens and the interface language; a hamburger under 900 px. |
| `components/Browse.svelte` | 77 | File browser dialog over the computer running the server (`/api/browse`), with an editable folder path. |
| `components/Transcribe.svelte` | 74 | Drop-down lists for model (shows size and whether it is downloaded), language and style; runs the transcribe job with progress. |
| `components/Player.svelte` | 121 | `<video>` + JASSUB (font preloaded, repaint on paused seeks); a `requestVideoFrameCallback` loop skips cut parts and tracks the current cue without reactive state at frame rate; keyboard shortcuts from `lib/shortcuts.json`. |
| `components/Toolbar.svelte` | 46 | The tool row under the video, with large touch-friendly buttons; the magnet toggles snapping. |
| `components/Inspector.svelte` | 49 | Edits the selected block: text (Esc leaves the box), start/end, split, merge, delete. |
| `components/Timeline.svelte` | 222 | wavesurfer.js waveform from the server's peaks; one draggable/resizable region per cue (diffed against the project), cuts and the in/out mark as overlays. While dragging, edges stick (8 px) to other cues' edges, the cue's own words, kept-range edges and the playhead, with a guide line; click selects and seeks, double-click jumps to the text; Ctrl + wheel zooms around the pointer. |
| `components/Drawer.svelte` | 43 | The optional side panel with tabs: `CueList`, `Glossary` + `Review`, `Cuts`, `Export`. |
| `components/CueList.svelte` | 74 | All cues as rows (text, times, split, merge, delete, add at playhead); dims cues inside cuts. |
| `components/Glossary.svelte` | 92 | Glossary library: choose or create the active one, add a word or `wrong -> right`, import a `.txt`, export. |
| `components/Review.svelte` | 57 | "Check" runs the glossary review on the current cues; apply or ignore each suggestion, or apply all (one undo step). |
| `components/Cuts.svelte`, `Export.svelte` | 31, 42 | Removed ranges with restore; MP4 / SRT / VTT / ASS export jobs with progress. |
| `lib/editor.svelte.ts` | 203 | `editor`: the project in `$state`, selection, snapshot undo/redo with grouping (800 ms per field), debounced autosave that then refreshes the preview `.ass`; commands `setText`, `setTimes`, `remove`, `split` (uses the words only while they still spell the text), `mergeNext`, `addAt`, `cut`, `restore`, `applySuggestions`; the in/out marks. |
| `lib/recovery.ts` | 67 | IndexedDB copy of the work (project, video path and size, `dirty` flag): `remember`, `lastWork`, `forget`, and `sameVideo` (the relink rule, ADR-018). |
| `lib/ui.svelte.ts` | 13 | Interface switches: snap on/off, which drawer panel is open. |
| `lib/player.ts` | 39 | Non-reactive handle on the `<video>` plus playback commands: `time`, `seek`, `togglePlay`, `cut`, `splitAtPlayhead`. |
| `lib/timeline.ts` | 103 | Kept-range math mirroring `project.py`: `normalize`, `removeRange`, `cutsOf`, `restoreRange`, `skipTarget`, `outputDuration`, `clock`; `snapPoints` / `snap` (binary search). Tested in `timeline.test.ts` (Vitest, incl. a random property test). |
| `lib/api.ts` | 122 | Types and calls: state, browse, open, upload (XHR with progress), glossary, peaks, review, save, preview `.ass`, `runJob` (POST + EventSource). |
| `lib/i18n.ts` | 38 | `t(key, vars)` over `locales/en.json` / `pt-BR.json` (language from the menu, remembered, else the browser's); `setLang`, `interfaceLanguages`. |
| `lib/shortcuts.json` | — | Editable key table: play, mark in/out, cut, split, snap, seek ±1 s, undo, redo. |
| `e2e/smoke.mjs` | 162 | Playwright test (`npm run e2e`, also in CI): starts `flosub serve` with no video, opens the clip through the file browser, then checks live snapping and its guide, the magnet button, double-click to edit, cut, undo, glossary add + apply, SRT export. |

### engine/legendaria_engine/__init__.py — 3 lines
Legendária transcription engine.

### engine/legendaria_engine/__main__.py — 5 lines
Allow `python -m legendaria_engine`.

### engine/legendaria_engine/ass.py — 137 lines
Styled subtitles: cues → Advanced SubStation Alpha (`.ass`), rendered by libass (ADR-012).

| Function / class | Line | What it does |
|---|---|---|
| `ass_color(rgba)` | 35 | RGBA floats (0 to 1) → `&HAABBGGRR` (ASS alpha 00 is opaque). |
| `ass_time(seconds)` | 42 | `H:MM:SS.cc` (centiseconds). |
| `escape(text)` | 51 | Cue text → ASS text: no override braces or backslashes; line breaks become `\N`. |
| `animation_tags(animation)` | 57 | Override tags for the cue's entrance (`pop`: scale from → peak → 100 %). |
| `to_ass(cues, look, size, line_length)` | 71 | The whole `.ass` file for these cues, drawn on a `size` (width, height) canvas. |

### engine/legendaria_engine/cli.py — 803 lines
`flosub` command line: transcribe, export, review, glossary, burn, overlay, serve, models, config.

| Function / class | Line | What it does |
|---|---|---|
| `output_path(stem, fmt)` | 18 | `<stem>.<fmt>`, or `<stem>.cues.json`; dots in the stem are kept (`a.b.mp4` → `a.b.srt`). |
| `write_outputs(transcript, stem, formats, config, style, size, cues)` | 24 | Write the requested formats next to `stem` (no extension); returns the paths. |
| `parse_size(value)` | 62 | argparse type: `WIDTHxHEIGHT` → (width, height). |
| `canvas_size(config, given, media)` | 74 | Canvas for `.ass`: `--size`, else the media's video size, else None (1920x1080). |
| `load_subtitles(path)` | 87 | A subtitle source: (transcript, cues, ass text); exactly one is set. |
| `ass_for(path, config, style, size)` | 97 | (.ass text, source media) from a transcript, a cues JSON or an `.ass` file. |
| `parse_clip(value)` | 111 | `START,END` in seconds → (start, end); raises ValueError on bad input. |
| `check_style(config, style)` | 122 | The style to use: `--style` if given, else the config default; must exist. |
| `parse_formats(value)` | 130 | argparse type: comma-separated format list, validated against FORMATS. |
| `cmd_transcribe(args, reporter)` | 141 | `flosub transcribe`: resolve config and model, transcribe, write the outputs. |
| `load_glossary(args, media, reporter)` | 211 | Global + project (next to `media`) + `--glossary` files, unless `--no-glossary`. |
| `wants_llm(config, flag)` | 224 | True/False when decided by the flag or config; None means "auto" (use it if reachable). |
| `run_review(transcript, glossary, config, stem, reporter, use_llm, llm_overrides)` | 237 | Glossary fixes (layer 2) and, when wanted, the LLM reviewer (layer 3). |
| `run_llm(transcript, glossary, review_cfg, reporter, use_llm, overrides)` | 289 | Layer 3 with graceful degradation: in auto mode an unreachable server just skips it. |
| `cmd_export(args, reporter)` | 323 | `flosub export`: a transcript (or an edited cues JSON) → cues / SRT / VTT / ASS. |
| `cmd_review(args, reporter)` | 339 | `flosub review FILE.json` (suggest or auto) and `flosub review apply FILE.review.json`. |
| `review_apply(path, args, reporter)` | 368 | Apply accepted suggestions (`--ids`, or every pending one with `--all`) to the transcript. |
| `cmd_llm(args, reporter)` | 402 | `flosub llm check|providers`: test the reviewer's server and list its models. |
| `cmd_glossary(args, reporter)` | 429 | `flosub glossary list|new|use|import|export|delete|show|path|add` (the glossary library). |
| `glossary_target(args)` | 520 | Where `glossary add` writes: --file, the project of --media, --name, or the active one. |
| `cmd_burn(args, reporter)` | 533 | `flosub burn VIDEO`: a copy of the video with the subtitles drawn in (FFmpeg + libass). |
| `cmd_overlay(args, reporter)` | 563 | `flosub overlay SUBS`: the subtitles alone on a transparent video (for editors). |
| `cmd_serve(args, reporter)` | 595 | `flosub serve [VIDEO]`: open the web editor, with a video or asking for one (plan 07). |
| `cmd_models(args, reporter)` | 607 | `flosub models list|download`. |
| `cmd_config(args, reporter)` | 634 | `flosub config show|path`. |
| `build_parser()` | 643 | The argparse tree for all subcommands. |
| `main(argv)` | 783 | Entry point: run a subcommand and turn every failure into an `error` event. |

### engine/legendaria_engine/config.py — 135 lines
Layered JSON configuration: shipped defaults → user file → command-line values.

| Function / class | Line | What it does |
|---|---|---|
| `class ConfigError` | 24 | A config file is malformed or holds an invalid value. |
| `read_json(path)` | 28 | Read a JSON object from a file, dropping `$schema`; raise ConfigError on bad JSON. |
| `deep_merge(base, override)` | 40 | Return `base` updated with `override`; nested objects are merged key by key. |
| `validate(config, source)` | 51 | Check the values the engine relies on, with errors that name the bad key. |
| `load_config(overrides)` | 102 | Defaults, then the user's `config.json` if present, then non-None `overrides`. |
| `update_user_config(changes)` | 114 | Merge `changes` into the user's config.json (creating it) and validate the result. |
| `load_models()` | 126 | The model catalog: shipped `models.json` plus the user's additions or changes. |

### engine/legendaria_engine/cuda_libs.py — 56 lines
Make the NVIDIA libraries installed by pip (cuBLAS, cuDNN) visible to CTranslate2.

| Function / class | Line | What it does |
|---|---|---|
| `nvidia_lib_dirs()` | 18 | Library folders of the installed `nvidia.*` packages (empty when not installed). |
| `ensure_cuda_libs()` | 33 | Expose the NVIDIA libraries to the current process. Call before importing ctranslate2. |

### engine/legendaria_engine/cues.py — 189 lines
Cues: the timed text blocks shown on screen, built from word timings by a style.

| Function / class | Line | What it does |
|---|---|---|
| `class Cue` | 21 | One block of text on screen, with the words it contains. |
| `class CueList` | 31 | Cues for one media file in one style (cues JSON v1). |
| `CueList.to_dict()` | 40 | Plain dict ready for JSON. |
| `CueList.save(path)` | 44 | Write as pretty UTF-8 JSON. |
| `CueList.from_dict(data)` | 49 | Build from a cues JSON v1 dict (words are optional). |
| `make_cues(transcript, style, style_name)` | 95 | Chunk the transcript's words into cues that respect the style's limits. |
| `wrap_lines(text, line_length)` | 182 | Split text into two balanced lines when it is longer than `line_length`. |

### engine/legendaria_engine/events.py — 111 lines
Progress reporting: JSON lines for programs (the Blender add-on), a progress bar for humans.

| Function / class | Line | What it does |
|---|---|---|
| `class Reporter` | 14 | Base reporter. Subclasses decide how events are shown. |
| `Reporter.emit(event, **data)` | 17 | Send one event. |
| `Reporter.progress(current, total)` | 21 | Transcription progress in seconds of media. |
| `Reporter.log(message)` | 25 | Informational message. |
| `Reporter.warning(message)` | 29 | Non-fatal problem (e.g. GPU fallback). |
| `Reporter.error(message)` | 33 | Fatal problem; the command exits with a non-zero code. |
| `Reporter.close()` | 37 | Release any resource (e.g. a progress bar). |
| `class JsonReporter` | 41 | Machine-readable events, one JSON object per line. |
| `JsonReporter.emit(event, **data)` | 47 | Write the event as one JSON line and flush, so readers see it at once. |
| `class HumanReporter` | 53 | Readable output on stderr, with a tqdm bar for transcription progress. |
| `HumanReporter.emit(event, **data)` | 61 | Render the event as text: progress bar, messages, saved files. |
| `HumanReporter.close()` | 102 | Close the progress bar, if any. |
| `make_reporter(mode)` | 107 | `json`, `human`, or `auto` (human when stdout is a terminal, JSON otherwise). |

### engine/legendaria_engine/formats.py — 37 lines
Subtitle writers: cues → SRT / VTT text (`.ass` lives in `ass.py`).

| Function / class | Line | What it does |
|---|---|---|
| `format_timestamp(seconds, separator)` | 10 | `HH:MM:SS,mmm` (SRT) or `HH:MM:SS.mmm` (VTT). Hours keep counting past 24. |
| `to_srt(cues, line_length)` | 19 | Numbered SRT blocks, one per cue; long cues wrap into two lines. |
| `to_vtt(cues, line_length)` | 28 | WebVTT blocks, one per cue; long cues wrap into two lines. |

### engine/legendaria_engine/media.py — 304 lines
FFmpeg: find it, read a video's size, burn subtitles in, cut + burn, render a transparent overlay.

| Function / class | Line | What it does |
|---|---|---|
| `class MediaError` | 25 | FFmpeg is missing or failed. |
| `find_tool(config, name)` | 29 | `ffmpeg` or `ffprobe`: next to the config's `ffmpeg` path (file or folder), else PATH. |
| `probe(path, config)` | 47 | Width, height, fps, duration and has_audio of a media file (width/height are None for audio). |
| `video_size(path, config)` | 87 | (width, height) of a video, or None for audio, a missing file or no ffprobe. |
| `run_ffmpeg(config, args, duration, reporter, cwd)` | 96 | Run FFmpeg with `args`, reporting progress from `-progress`; raise MediaError on failure. |
| `burn(config, video, ass_text, output, reporter)` | 144 | Burn the subtitles into a copy of `video` (encoder settings from config `burn`). |
| `overlay(config, ass_text, size, fps, duration, output, reporter)` | 173 | Render the subtitles alone on a transparent canvas (QuickTime Animation, argb). |
| `cut_graph(keep, audio, subs)` | 209 | Filter graph: trim each kept range, concat them, then burn `subs` (outputs [vo], [ao]). |
| `render(config, video, keep, ass_text, output, reporter)` | 224 | One FFmpeg pass: keep only `keep` (source seconds), burn `ass_text` (output time) if given. |
| `peaks(config, path, per_sec, rate)` | 270 | Waveform peaks: the largest |sample| (0 to 1) in each 1/`per_sec` s, decoded by FFmpeg. |

### engine/legendaria_engine/models.py — 105 lines
List, download and locate Whisper models (stored in the per-OS data dir).

| Function / class | Line | What it does |
|---|---|---|
| `model_path(name)` | 23 | Folder where a catalog model is (or will be) stored. |
| `is_installed(name)` | 28 | True when the model folder has all the files CTranslate2 needs. |
| `list_models()` | 34 | Catalog entries with an `installed` flag, in catalog order. |
| `download(name, reporter)` | 70 | Download a catalog model into the data dir; returns its folder. |
| `resolve(name, reporter)` | 96 | Folder of an installed model, downloading it first when needed. |

### engine/legendaria_engine/paths.py — 42 lines
Per-OS locations for user config, data and models.

| Function / class | Line | What it does |
|---|---|---|
| `config_dir()` | 13 | Directory of the user config file; `LEGENDARIA_CONFIG_DIR` overrides it. |
| `data_dir()` | 19 | Directory for downloaded models and other data; `LEGENDARIA_DATA_DIR` overrides it. |
| `user_config_file()` | 25 | The user config overrides: `<config dir>/config.json`. |
| `user_models_file()` | 30 | User additions to the model catalog: `<config dir>/models.json`. |
| `models_dir()` | 35 | Where downloaded models live: `<data dir>/models`. |
| `defaults_dir()` | 40 | Shipped default JSON files inside the package. |

### engine/legendaria_engine/project.py — 192 lines
Project file: the web editor's document, `<video>.legendaria.json` (ADR-016).

| Function / class | Line | What it does |
|---|---|---|
| `class ProjectError` | 28 | The project file is missing, unreadable or invalid. |
| `project_path(video)` | 32 | `clip.mp4` → `clip.mp4.legendaria.json`, next to the video. |
| `normalize(ranges, duration)` | 37 | Sort, clip to [0, duration], merge overlapping ranges and drop empty ones. |
| `remove_range(keep, start, end)` | 51 | The kept ranges after cutting out [start, end] (source time); tiny cuts are ignored. |
| `output_duration(keep)` | 67 | Length of the edited video: the sum of the kept ranges. |
| `remap(cues, keep)` | 72 | Cues on the output timeline: removed parts disappear, cues across a cut are clipped. |
| `class Project` | 87 | The editor document. `source` is relative to the project file when possible. |
| `Project.new(video, duration, cues)` | 98 | A fresh project for `video`: nothing cut, the cues as transcribed. |
| `Project.cue_list()` | 109 | The cues (source time) as a CueList. |
| `Project.edited_cues()` | 113 | The cues on the output timeline (after the cuts). |
| `Project.to_dict()` | 117 | Plain dict ready for JSON (see schemas/project.schema.json). |
| `Project.from_dict(data)` | 131 | Validate and build; ranges are normalized, cues sorted by start. |
| `Project.load(path)` | 169 | Read a project file. |
| `Project.save(path)` | 177 | Write atomically (temp file + rename), so a crash never leaves half a project. |

### engine/legendaria_engine/schema.py — 115 lines
Transcript format (JSON v1): the contract between the engine and the Blender add-on.

| Function / class | Line | What it does |
|---|---|---|
| `class Word` | 14 | One recognized word with its timing (seconds) and confidence. |
| `class Segment` | 24 | A sentence-like chunk of speech; becomes one subtitle cue. |
| `class Transcript` | 34 | The whole transcription of one media file (JSON v1). |
| `Transcript.to_dict()` | 46 | Plain dict ready for JSON. |
| `Transcript.from_dict(data)` | 51 | Build from a dict, rejecting other schema versions. |
| `Transcript.merged_with(update, start, end)` | 72 | A copy of this transcript where [start, end] comes from `update`. |
| `Transcript.save(path)` | 108 | Write as pretty UTF-8 JSON. |
| `Transcript.load(path)` | 113 | Read a transcript JSON file. |

### engine/legendaria_engine/server.py — 574 lines
`flosub serve`: the local web editor's backend (plan 07, ADR-014).

| Function / class | Line | What it does |
|---|---|---|
| `class Job` | 55 | A background task (transcribe, export) that records its events for SSE readers. |
| `Job.emit(event, **data)` | 65 | Record one event and wake the SSE readers. |
| `Job.wait(seen, timeout)` | 73 | Events after the first `seen` ones; blocks up to `timeout` for new ones. |
| `class Session` | 81 | One video being edited: its project file, config and running jobs. |
| `Session.project()` | 93 | The saved project, or None before the first transcription. |
| `Session.state()` | 97 | Everything the editor needs on load. |
| `Session.peaks()` | 110 | Waveform peaks (100 per second), computed once per session. |
| `Session.review()` | 120 | Glossary suggestions (layer 2, no AI) for the saved cues, as the editor shows them. |
| `Session.look(style)` | 160 | The style's `.ass` look from the config (empty if unknown). |
| `Session.size()` | 164 | The video's (width, height) for the `.ass` canvas. |
| `Session.ass_text(cues, style)` | 168 | `.ass` for these cues in the style's look, on the video's canvas. |
| `Session.start(kind, work)` | 173 | Run `work(job)` in a thread; only one job at a time. |
| `Session.transcribe(job, options)` | 190 | Run `flosub transcribe` in a child process (it may re-exec for CUDA), relay events. |
| `Session.export(job, fmt)` | 233 | Write the edited video (`mp4`) or subtitles (`srt`, `vtt`, `ass`) next to the source. |
| `find_font(name, bold)` | 262 | The font file the system uses for `name` (fontconfig), so the preview matches FFmpeg. |
| `class Handler` | 275 | Routes for the editor. `self.server.session` is the open video. |
| `Handler.session()` | 282 | The open video's session (routes that need one are guarded by `_ready`). |
| `Handler.log_message(format, *args)` | 293 | Quiet: only errors are printed. |
| `Handler.do_GET()` | 328 | Static app, state, media, font, preview `.ass` and job events. |
| `Handler.do_PUT()` | 374 | Save the project (validated and normalized); returns what was saved. |
| `Handler.do_POST()` | 389 | Start a job: `/api/transcribe` {model, language, style} or `/api/export` {format}. |
| `make_server(video, port, config)` | 546 | A server on 127.0.0.1 (`port` 0 picks a free one), with `video` open if given. |
| `serve(video, port, open_browser, reporter)` | 557 | Run the editor until Ctrl+C (the browser asks for a video when none is given). |

### engine/legendaria_engine/transcriber.py — 145 lines
Speech-to-text. A small backend interface keeps room for other engines (e.g. Apple Silicon).

| Function / class | Line | What it does |
|---|---|---|
| `class Options` | 14 | Everything a backend needs to run one transcription. |
| `class Backend` | 29 | Interface for speech-to-text engines (faster-whisper today; Apple Silicon later). |
| `Backend.transcribe(media, options, reporter)` | 34 | Transcribe `media`, reporting progress, and return the transcript. |
| `cuda_available()` | 39 | True when CTranslate2 sees at least one CUDA device. |
| `class FasterWhisperBackend` | 49 | faster-whisper (CTranslate2): CUDA on NVIDIA GPUs, int8 on CPU. |
| `FasterWhisperBackend.transcribe(media, options, reporter)` | 59 | Try each device in turn; in `auto` mode a GPU failure falls back to the CPU. |
| `get_backend(name)` | 141 | Instantiate a backend by name. |

### engine/legendaria_engine/workspace.py — 129 lines
What the web editor needs besides the open video: a file browser, the model and language

| Function / class | Line | What it does |
|---|---|---|
| `uploads_dir()` | 20 | Where dropped files are stored: `<data dir>/uploads/` (a browser cannot give us the original path). |
| `browse(path)` | 25 | The folders and media files in `path` (default: the home folder), folders first. |
| `languages()` | 52 | Language codes for the transcribe form: the defaults, or `<config dir>/languages.json` if present. |
| `options(config)` | 59 | Choices and defaults for the transcribe form. |
| `glossary_state()` | 74 | The glossary library: names, which one is active, and the active one's text. |
| `glossary_add(entry)` | 85 | Add a term or a `wrong -> right` line to the active glossary; False if already there. |
| `glossary_import(name, text, activate)` | 92 | Save `text` as the glossary `name` (merging into it when it exists); returns the name. |
| `glossary_use(name)` | 105 | Make `name` the active glossary (created empty if new). |
| `glossary_text(name)` | 113 | The text of a library glossary, for export. |

### engine/legendaria_engine/review/__init__.py — 1 lines
Accuracy tools: glossary, transcription bias, deterministic fixes, suggestions (plan 03).

### engine/legendaria_engine/review/align.py — 41 lines
Replace words in a transcript and give the new words sensible timings.

| Function / class | Line | What it does |
|---|---|---|
| `retime(old, new_text)` | 8 | Words for `new_text` spread over the time span of `old`, in proportion to length. |
| `segment_text(words)` | 31 | Segment text rebuilt from its words (as Whisper spells them). |
| `replace_words(segment, first, last, new_text)` | 36 | A copy of `segment` with words[first:last] replaced by `new_text`. |

### engine/legendaria_engine/review/bias.py — 22 lines
Layer 1: glossary terms as Whisper `hotwords`, which steer recognition toward them.

| Function / class | Line | What it does |
|---|---|---|
| `hotwords(glossary, max_chars)` | 12 | Comma-separated terms within the budget, or None when there are none. |

### engine/legendaria_engine/review/fix_rules.py — 102 lines
Layer 2: glossary-based corrections without AI.

| Function / class | Line | What it does |
|---|---|---|
| `match_case(original, replacement)` | 25 | Keep a capital first letter from the original ("Bolsa Bet" + "bolsa Beth" → "Bolsa Beth"). |
| `similarity(a, b)` | 36 | Ratio of two strings after folding case, accents and edge punctuation. |
| `suggest(transcript, glossary, threshold, low_confidence, start_id)` | 41 | Suggestions for every segment; explicit fixes first, then fuzzy matches. |

### engine/legendaria_engine/review/glossary.py — 234 lines
Glossary files: names and terms the transcription must get right.

| Function / class | Line | What it does |
|---|---|---|
| `fold(text)` | 31 | Lowercase without accents or surrounding punctuation, for comparisons. |
| `split_entry(line)` | 38 | A parsed line: (wrong, right), a term, or None for blanks and comments. |
| `class Glossary` | 51 | Merged terms (in order, unique) and explicit fixes keyed by folded wrong text. |
| `Glossary.add_term(term)` | 58 | Add a term unless an equal one (ignoring case and accents) is there. |
| `Glossary.merge_text(text)` | 63 | Add every entry of a glossary file's text. |
| `library_dir()` | 82 | Named glossaries live here: `<config dir>/glossaries/<name>.txt`. |
| `safe_name(name)` | 87 | A glossary name usable as a file name on every OS (raises ValueError otherwise). |
| `library_file(name)` | 95 | File of a named glossary (it may not exist yet). |
| `migrate_legacy()` | 100 | An old single `<config dir>/glossary.txt` becomes the glossary named "default". |
| `list_names()` | 109 | Names of the glossaries in the library, sorted. |
| `active_name()` | 116 | The active glossary (config `review.glossary`, default "default"). |
| `global_file()` | 123 | The active library glossary, used for every project. |
| `resolve(ref)` | 129 | A glossary given as a file path or as the name of a library glossary. |
| `create(name)` | 143 | A new empty library glossary (with the explanatory header). |
| `import_file(source, name, overwrite)` | 153 | Copy a glossary file into the library (named after the file unless `name`). |
| `export_file(name, destination)` | 167 | Copy a library glossary to a file (to share it or back it up). |
| `delete(name)` | 178 | Remove a library glossary. |
| `project_file(media)` | 186 | The glossary next to a media file: `legendaria-glossary.txt`. |
| `load(extra, media, use_global)` | 191 | Active library glossary, then the project one next to `media`, then `extra` |
| `add_entry(path, entry)` | 212 | Append a term or a 'wrong -> right' line; returns False if it was already there. |

### engine/legendaria_engine/review/llm.py — 153 lines
Layer 3: an LLM reviewer over any OpenAI-compatible chat server (Ollama, LM Studio,

| Function / class | Line | What it does |
|---|---|---|
| `class LLMError` | 19 | The LLM server is unreachable, refused the request, or answered nonsense. |
| `class LLMSettings` | 24 | Where and how to call the reviewer model. |
| `load_providers()` | 35 | Shipped provider presets plus the user's `<config dir>/providers.json`. |
| `resolve(llm_config, **overrides)` | 44 | Settings from config `review.llm` plus overrides (provider, base_url, model). |
| `class LLMClient` | 63 | Minimal chat-completions client. |
| `LLMClient.list_models()` | 93 | Model ids the server offers (`GET /models`). |
| `LLMClient.pick_model()` | 98 | The configured model, or the first chat model the server lists. |
| `LLMClient.chat_json(prompt)` | 108 | Send one user message and parse the JSON object in the answer. |
| `LLMClient.unload()` | 129 | Ollama only: free the model from GPU memory now (it would stay for 5 minutes). |
| `parse_json_object(text)` | 142 | The JSON object in a model answer, tolerating code fences or text around it. |

### engine/legendaria_engine/review/reviewer.py — 232 lines
Layer 3: turn an LLM's corrected lines into guarded, word-level suggestions.

| Function / class | Line | What it does |
|---|---|---|
| `class Unit` | 27 | A readable word: one or more Whisper words glued together ("bem" + "-vindas"). |
| `units_of(words)` | 36 | Group a segment's words into readable units. |
| `guard(old, new, glossary, low_confidence)` | 65 | Why a changed block is acceptable, or None to reject it. |
| `line_for_prompt(units, low_confidence)` | 88 | Line text with uncertain words marked [[like this]]. |
| `diff_suggestions(seg_index, segment, corrected, glossary, low_confidence, max_change_ratio)` | 93 | (suggestions, rejected count) for one segment and the model's version of it. |
| `build_prompt(lines, targets, language, glossary)` | 144 | Fill the editable prompt template (`defaults/review_prompt.txt`, user copy wins). |
| `fixes_by_line(answer, count)` | 161 | {0-based line offset: corrected text} from {"fixes": {"<1-based n>": text}}. |
| `review(transcript, client, glossary, reporter, low_confidence, batch_lines, context_lines, max_change_ratio)` | 180 | LLM suggestions for the whole transcript; returns (suggestions, rejected count). |
| `describe(settings)` | 228 | Short provider/model label for logs. |

### engine/legendaria_engine/review/suggestions.py — 89 lines
Review document (`<name>.review.json`, v1): suggested corrections to accept or reject.

| Function / class | Line | What it does |
|---|---|---|
| `class Suggestion` | 18 | Replace words[first:last] of one segment ("before") with "after". |
| `class Review` | 35 | All suggestions for one transcript file. |
| `Review.to_dict()` | 42 | Plain dict ready for JSON. |
| `Review.save(path)` | 46 | Write as pretty UTF-8 JSON. |
| `Review.load(path)` | 51 | Read a review JSON file. |
| `apply(transcript, suggestions)` | 62 | A copy of the transcript with the given suggestions applied (word timings re-spread). |


**Blender add-on data files:**
- `blender_addon/legendaria/blender_manifest.toml`: extension id `legendaria`, Blender ≥ 4.2, GPL-3.0-or-later, permissions (files, network via the engine).
- `blender_addon/legendaria/presets/pop.json` (yellow, bold, outline — MVP default), `captions.json`, `subtitles.json`: text-strip styles (font size for 1080 px, scaled to the scene; position, alignment, outline, shadow, box). A user copy in `<config dir>/presets/` overrides them.
- `blender_addon/legendaria/locales/pt_BR.json` (+ README): UI translations, English source strings as keys.
- `blender_addon/tests/`: `test_i18n.py` (every UI string translated, no unused or mismatched entries), `test_installer.py` (uv asset names, checksum, extraction, versions), `test_source_rules.py` (Blender API pitfalls, e.g. confirm-dialog icons), `test_timecode.py`, `test_engine_bridge.py` (fake flosub), `conftest.py` (imports the add-on package without bpy), `blender_smoke.py` (headless, inside Blender, with a throwaway config folder; glossary library, review, Export ASS and exact-preview checks; `--real` runs flosub, review and apply), `ui_walkthrough.py` (GUI session with screenshots under xvfb; `--install confirm|run` tests the Install engine flow).

### blender_addon/legendaria/__init__.py — 36 lines
Legendária: automatic CapCut-style subtitles in Blender's Video Sequencer.

| Function / class | Line | What it does |
|---|---|---|
| `register()` | 22 | Register everything and look for the engine shortly after Blender is ready. |
| `unregister()` | 30 | Unregister everything (also cancels a pending engine lookup). |

### blender_addon/legendaria/compat.py — 76 lines
VSE API differences between Blender 4.2 and 5.x, detected by feature, not version.

| Function / class | Line | What it does |
|---|---|---|
| `top_strips(editor)` | 13 | Top-level strips collection (supports `new_effect` and `remove`). |
| `all_strips(editor)` | 18 | All strips, including those inside meta strips. |
| `new_text_strip(editor, name, channel, frame_start, frame_end)` | 23 | Create a TEXT effect strip covering [frame_start, frame_end). |
| `remove_strip(editor, strip)` | 41 | Delete a strip. |
| `set_alignment(strip, align_x, align_y)` | 46 | Horizontal/vertical text alignment around the strip's location. |
| `set_if_present(strip, name, value)` | 60 | Set a property when this Blender version has it; returns whether it was set. |
| `media_path(strip)` | 68 | Absolute file path of a MOVIE or SOUND strip ('' for other types). |

### blender_addon/legendaria/engine_bridge.py — 209 lines
Find and run the `flosub` engine as a separate process (ADR-003). No bpy here.

| Function / class | Line | What it does |
|---|---|---|
| `user_data_dir()` | 23 | Same per-OS data folder the engine uses (platformdirs, appauthor=False). |
| `user_config_dir()` | 32 | Same per-OS config folder the engine uses (platformdirs, appauthor=False). |
| `managed_engine()` | 41 | Where the add-on's "Install engine" step (stage 2b) puts flosub. |
| `candidate_paths()` | 47 | Usual per-user install locations that Blender's PATH may not include. |
| `find_engine(custom)` | 59 | The flosub executable: custom path (file or folder), managed install, PATH, user dirs. |
| `version_key(text)` | 75 | Sortable key for versions like "0.1.0", "0.1.0.dev1" or "flosub 0.2.0" (dev < final). |
| `run_json(engine, args, timeout)` | 97 | Run a quick command that prints one JSON document (e.g. `models list --json`). |
| `run_text(engine, args, timeout)` | 105 | Run a quick command and return its stdout (e.g. `--version`). |
| `run_events(engine, args, timeout)` | 113 | Run a quick command with JSON-lines events; raise RuntimeError on an `error` event. |
| `class EngineJob` | 133 | A running `flosub --progress json ...` process whose events can be polled. |
| `EngineJob.poll()` | 161 | Events received since the last call (never blocks). |
| `EngineJob.finished()` | 171 | True once the process has exited and all of its output has been read. |
| `EngineJob.returncode()` | 176 | Exit code, or None while running. |
| `EngineJob.stderr_tail()` | 180 | Last lines the engine wrote to stderr (for error reports). |
| `EngineJob.cancel()` | 184 | Stop the engine: terminate, then kill if it does not exit quickly. |
| `EngineJob.wait(timeout)` | 205 | Block until the process exits and its output is read (tests and scripts, not the UI). |

### blender_addon/legendaria/i18n.py — 46 lines
UI translations (ADR-005): English source strings, `locales/<lang>.json` dictionaries.

| Function / class | Line | What it does |
|---|---|---|
| `load_translations()` | 19 | {blender_locale: {(context, english): translated}} from every locales/*.json. |
| `N_(text)` | 29 | Mark a string for translation without translating it yet (translate when shown). |
| `tr(text)` | 34 | Translate a dynamic UI string (reports, formatted messages) for the current locale. |
| `register(package)` | 39 | Register the dictionaries under the add-on's package name. |
| `unregister(package)` | 44 | Remove the dictionaries. |

### blender_addon/legendaria/installer.py — 288 lines
The "Install engine" step: set up flosub for users who never open a terminal (plan 02, 2b).

| Function / class | Line | What it does |
|---|---|---|
| `N_(text)` | 38 | Mark a UI message for translation; the add-on translates it when it shows it. |
| `engine_root()` | 43 | The single folder that holds everything the installer creates. |
| `uv_asset(system, machine)` | 48 | Release asset name of uv for an OS / CPU pair (defaults to this machine). |
| `has_nvidia_gpu()` | 60 | True when `nvidia-smi` lists a GPU (Linux / Windows; never on macOS). |
| `wants_cuda()` | 73 | Install GPU support? `LEGENDARIA_INSTALL_CUDA=0|1` decides, else NVIDIA detection. |
| `extract_uv(archive, asset, target_dir)` | 81 | Write the uv executable from a release archive into `target_dir`. |
| `verify_sha256(data, checksum_file)` | 98 | Raise unless `data` matches the first hex digest in a `.sha256` file. |
| `class Installer` | 106 | Runs the install steps on a background thread; `state` is safe to read anytime. |
| `Installer.start()` | 137 | Begin installing in the background. |
| `Installer.cancel()` | 142 | Stop after the current step (the running command is terminated). |
| `Installer.join(timeout)` | 148 | Wait for the background thread (tests and scripts). |
| `Installer.running()` | 154 | True while the background thread is working. |
| `is_installed()` | 270 | True when the managed engine exists. |
| `uninstall()` | 275 | Delete everything the installer created (models live elsewhere and are kept). |

### blender_addon/legendaria/operators.py — 669 lines
Operators: generate (runs the engine without blocking), cancel, re-apply style, export, refresh.

| Function / class | Line | What it does |
|---|---|---|
| `cache_dir()` | 18 | Where transcripts and cues are saved: `//legendaria/` next to the .blend, else a temp folder. |
| `redraw_sequencer(context)` | 25 | Refresh sequencer areas so progress shows up. |
| `class Plan` | 33 | What a generate / re-apply run will do; built and validated before anything starts. |
| `Plan.pick_range(scene)` | 84 | Range to regenerate: the scene's preview range, else the selected captions. |
| `Plan.confirm_message()` | 98 | Warning shown before replacing captions (owner requirement R3). |
| `engine_or_error()` | 117 | The detected engine, refreshing the cache once if needed. |
| `colors_are_exact(scene)` | 130 | True when the scene shows colors as they are (no Filmic/AgX tone mapping). |
| `use_exact_colors(scene)` | 135 | Switch the scene to the Standard view transform; returns True if it changed. |
| `finish_strips(context, plan, cues_path, style)` | 147 | Create the caption strips from a cues file and remember where they came from. |
| `class LEGENDARIA_OT_generate` | 159 | Transcribe the selected strip and create caption strips |
| `LEGENDARIA_OT_generate.make_plan(context)` | 173 | Plan for the whole media, or for a range of the last generated media. |
| `LEGENDARIA_OT_generate.poll(context)` | 185 | Needs a scene with settings and no job already running. |
| `LEGENDARIA_OT_generate.invoke(context, event)` | 189 | Validate, then ask before replacing existing captions. |
| `LEGENDARIA_OT_generate.execute(context)` | 208 | Start the engine and the modal timer. |
| `LEGENDARIA_OT_generate.handle_event(event)` | 242 | Update progress and status from one engine event. |
| `LEGENDARIA_OT_generate.modal(context, event)` | 280 | Poll the engine on each timer tick; Esc or the Cancel button stops it. |
| `LEGENDARIA_OT_generate.cleanup(context)` | 321 | Remove the timer and mark the job as stopped. |
| `class LEGENDARIA_OT_cancel` | 331 | Stop the running transcription |
| `LEGENDARIA_OT_cancel.execute(context)` | 337 | Ask the running generate operator to stop. |
| `class LEGENDARIA_OT_reapply_style` | 343 | Rebuild the captions from the saved transcript with the chosen style, without transcribing again |
| `LEGENDARIA_OT_reapply_style.poll(context)` | 351 | Needs a saved transcript and no running job. |
| `LEGENDARIA_OT_reapply_style.invoke(context, event)` | 356 | Ask before replacing captions. |
| `LEGENDARIA_OT_reapply_style.execute(context)` | 374 | Run `flosub export --style` on the saved transcript and rebuild the strips. |
| `render_size(scene)` | 417 | The render size as `WIDTHxHEIGHT` (the canvas of `.ass` files and overlays). |
| `export_ass(context, cues, path)` | 422 | Write `.ass` from the edited captions through the engine (the look of the style). |
| `class LEGENDARIA_OT_export` | 432 | Save the captions on the channel as an SRT, VTT or ASS file (with your edits) |
| `LEGENDARIA_OT_export.export_channel(context)` | 449 | Channel to export: the one used last, else the setting, else the active strip's. |
| `LEGENDARIA_OT_export.invoke(context, event)` | 455 | Open the file browser with a sensible default name. |
| `LEGENDARIA_OT_export.execute(context)` | 466 | Write the file from the text strips. |
| `class LEGENDARIA_OT_exact_colors` | 497 | Use the Standard view transform so captions keep their real colors |
| `LEGENDARIA_OT_exact_colors.execute(context)` | 504 | Switch the scene's view transform to Standard. |
| `class LEGENDARIA_OT_refresh_engine` | 511 | Look for the transcription engine again and reload its models |
| `LEGENDARIA_OT_refresh_engine.execute(context)` | 517 | Re-run engine detection. |
| `install_status()` | 526 | Translated status line and progress of the running install (for panel and preferences). |
| `class LEGENDARIA_OT_install_engine` | 536 | Download and set up the transcription engine (uv, Python, flosub and the default model) |
| `LEGENDARIA_OT_install_engine.poll(context)` | 545 | Not while an install is already running. |
| `LEGENDARIA_OT_install_engine.invoke(context, event)` | 549 | Explain what will be downloaded and ask first. |
| `LEGENDARIA_OT_install_engine.execute(context)` | 569 | Start the installer thread and poll it from a timer. |
| `LEGENDARIA_OT_install_engine.modal(context, event)` | 579 | Redraw while installing; report the result at the end. |
| `class LEGENDARIA_OT_cancel_install` | 602 | Stop installing the engine |
| `LEGENDARIA_OT_cancel_install.execute(context)` | 608 | Ask the installer to stop. |
| `class LEGENDARIA_OT_uninstall_engine` | 615 | Delete the engine installed by this add-on (downloaded models are kept) |
| `LEGENDARIA_OT_uninstall_engine.poll(context)` | 622 | Only when the add-on's own engine is installed and idle. |
| `LEGENDARIA_OT_uninstall_engine.invoke(context, event)` | 626 | Ask first. |
| `LEGENDARIA_OT_uninstall_engine.execute(context)` | 639 | Remove the engine folder and look for another engine. |
| `register()` | 660 | Register the operators. |
| `unregister()` | 666 | Remove the operators. |

### blender_addon/legendaria/panel.py — 174 lines
Sidebar panel in the Video Sequencer ("Legendária" tab).

| Function / class | Line | What it does |
|---|---|---|
| `draw_engine_box(layout)` | 12 | Engine install / update / progress UI. Returns True when the engine is ready to use. |
| `draw_review_box(layout, settings)` | 44 | Glossary picker (new / import / export / edit / add) and the review suggestions. |
| `class LEGENDARIA_PT_main` | 83 | Generate, re-style and export captions |
| `LEGENDARIA_PT_main.draw(context)` | 92 | Engine status, source, options, generate/progress, re-style and export. |
| `register()` | 165 | Register the panel. |
| `unregister()` | 171 | Remove the panel. |

### blender_addon/legendaria/preferences.py — 51 lines
Add-on preferences: where the engine is, and its detected status.

| Function / class | Line | What it does |
|---|---|---|
| `class LegendariaPreferences` | 11 | Shown under Edit → Preferences → Add-ons → Legendária. |
| `LegendariaPreferences.draw(context)` | 23 | Engine path, detection result and a refresh button. |
| `register()` | 42 | Register the preferences class. |
| `unregister()` | 48 | Remove the preferences class. |

### blender_addon/legendaria/preview_ops.py — 214 lines
Exact preview (plan 04 §10): the captions rendered by libass, shown above the strips.

| Function / class | Line | What it does |
|---|---|---|
| `overlay_strips(editor)` | 25 | The exact-preview movie strips in the editor. |
| `free_channel_above(editor, channel, start, end)` | 30 | First channel above `channel` with nothing between `start` and `end`. |
| `caption_channel(context)` | 41 | The captions channel: the one used last, else the setting. |
| `remove_overlay(context)` | 47 | Delete the preview movie(s), unmute the captions channel; returns how many were removed. |
| `place_overlay(context, movie, channel)` | 65 | Put the rendered `.mov` above the captions with Alpha Over and mute the captions. |
| `class LEGENDARIA_OT_exact_preview` | 81 | Show the captions exactly as the final video will look (font, colors, pop animation). Run it again after editing |
| `LEGENDARIA_OT_exact_preview.poll(context)` | 94 | Needs captions and no running job. |
| `LEGENDARIA_OT_exact_preview.execute(context)` | 103 | Write the strips as cues and start `flosub overlay` in the background. |
| `LEGENDARIA_OT_exact_preview.modal(context, event)` | 142 | Follow the render; place the movie when it is done. |
| `class LEGENDARIA_OT_remove_preview` | 187 | Remove the exact preview and show the editable caption strips again |
| `LEGENDARIA_OT_remove_preview.execute(context)` | 194 | Delete the overlay movie and unmute the captions. |
| `register()` | 205 | Register the preview operators. |
| `unregister()` | 211 | Remove them. |

### blender_addon/legendaria/properties.py — 225 lines
Scene settings and the engine info cache (models, languages, styles from `flosub`).

| Function / class | Line | What it does |
|---|---|---|
| `addon_prefs(context)` | 40 | The add-on preferences, or None when the add-on is not enabled through Preferences. |
| `refresh_engine_info(context)` | 47 | Locate flosub and reload models, languages and styles. Returns True when found. |
| `refresh_glossaries(engine)` | 92 | Reload the glossary library (names, sizes, active one) from the engine. |
| `class LegendariaSuggestion` | 146 | One suggested correction from `flosub review`. |
| `class LegendariaSettings` | 159 | Per-scene options and the state of the running job. |
| `register()` | 214 | Register the settings and attach them to scenes. |
| `unregister()` | 221 | Remove the settings. |

### blender_addon/legendaria/review_ops.py — 441 lines
Glossary and review operators (plan 03, stage 3c): thin wrappers around the engine.

| Function / class | Line | What it does |
|---|---|---|
| `class LEGENDARIA_OT_glossary_new` | 38 | Create a new, empty glossary and make it the active one |
| `LEGENDARIA_OT_glossary_new.invoke(context, event)` | 46 | Ask for the name. |
| `LEGENDARIA_OT_glossary_new.execute(context)` | 50 | `flosub glossary new NAME --activate`. |
| `class LEGENDARIA_OT_glossary_import` | 62 | Add a glossary file (.txt) to your glossaries and make it the active one |
| `LEGENDARIA_OT_glossary_import.invoke(context, event)` | 71 | Open the file browser. |
| `LEGENDARIA_OT_glossary_import.execute(context)` | 76 | `flosub glossary import FILE`, then `use` it. |
| `class LEGENDARIA_OT_glossary_export` | 89 | Save the active glossary to a file, to share it or keep a copy |
| `LEGENDARIA_OT_glossary_export.invoke(context, event)` | 98 | Open the file browser with the glossary's name. |
| `LEGENDARIA_OT_glossary_export.execute(context)` | 104 | `flosub glossary export NAME --to FILE`. |
| `class LEGENDARIA_OT_glossary_edit` | 116 | Open the active glossary in your text editor (one term per line, or 'wrong -> right') |
| `LEGENDARIA_OT_glossary_edit.execute(context)` | 122 | Create the file if needed and open it with the system's editor. |
| `class LEGENDARIA_OT_glossary_add` | 135 | Add a word or name to a glossary, so the next transcriptions and reviews get it right |
| `LEGENDARIA_OT_glossary_add.invoke(context, event)` | 151 | Prefill with the selected caption's text, then let the user trim it. |
| `LEGENDARIA_OT_glossary_add.execute(context)` | 160 | `flosub glossary add TERM [--media VIDEO]`. |
| `class LEGENDARIA_OT_review` | 193 | Look for transcription errors using the glossary (and, if enabled, an AI model) and list suggested corrections |
| `LEGENDARIA_OT_review.poll(context)` | 205 | Needs a transcript from a previous run and no running job. |
| `LEGENDARIA_OT_review.execute(context)` | 210 | Start `flosub review` in the background. |
| `LEGENDARIA_OT_review.modal(context, event)` | 234 | Poll the engine; fill the suggestions list when it is done. |
| `load_suggestions(settings, review_path)` | 283 | Fill the scene's suggestion list from a review file; returns how many are pending. |
| `class LEGENDARIA_OT_review_select` | 300 | Tick or untick every suggestion |
| `LEGENDARIA_OT_review_select.execute(context)` | 308 | Set `accept` on every listed suggestion. |
| `merged_ranges(spans)` | 315 | Merge overlapping or touching frame ranges. |
| `correction_spans(scene, plan, cues, chosen)` | 326 | Frame spans to rebuild: every old caption and new cue touching a corrected word. |
| `class LEGENDARIA_OT_review_apply` | 350 | Apply the ticked corrections: the transcript is updated and only the affected captions are rebuilt |
| `LEGENDARIA_OT_review_apply.poll(context)` | 358 | Needs suggestions and no running job. |
| `LEGENDARIA_OT_review_apply.execute(context)` | 363 | `flosub review apply`, re-export cues, rebuild the strips in each corrected span. |
| `class LEGENDARIA_UL_suggestions` | 404 | Suggested corrections: tick to accept, + to add the corrected word to the glossary. |
| `LEGENDARIA_UL_suggestions.draw_item(context, layout, data, item, icon, active_data, active_propname, index)` | 407 | One row: checkbox, before → after, add-to-glossary button. |
| `register()` | 432 | Register the glossary and review operators. |
| `unregister()` | 438 | Remove them. |

### blender_addon/legendaria/strips.py — 215 lines
Cues ↔ text strips: create caption strips, find the ones we made, read them back.

| Function / class | Line | What it does |
|---|---|---|
| `scene_fps(scene)` | 17 | Real frames per second (fps / fps_base). |
| `load_preset(style)` | 22 | Strip style for a cue style: user override in the config dir, else the shipped preset. |
| `short_side(scene)` | 31 | The render's shorter side in pixels (1080 for both 1920x1080 and 1080x1920). |
| `apply_preset(strip, preset, short)` | 36 | Apply a style preset to a text strip; font sizes are for a 1080 px short side. |
| `is_ours(strip)` | 61 | True for strips created by the add-on. |
| `overlaps(strip, frame_start, frame_end)` | 66 | Whether the strip's visible range intersects [frame_start, frame_end). |
| `tagged_in_range(editor, channel, frame_start, frame_end, by_midpoint)` | 71 | Our caption strips on `channel` in the range (they would be replaced). |
| `foreign_in_range(editor, channel, frame_start, frame_end)` | 90 | Strips not made by us on `channel` in the range (we never touch these). |
| `pick_channel(editor, media_strip, frame_start, frame_end)` | 99 | First channel above the media strip that holds only our captions (or nothing) in range. |
| `media_range(media_strip)` | 107 | (content_start, visible_start, visible_end) frames of a MOVIE/SOUND strip. |
| `load_cues(path)` | 115 | Read a cues JSON (v1) written by `flosub ... --format cues`. |
| `create_strips(scene, editor, cues, media_strip, channel, style, frame_range)` | 123 | Replace our strips on `channel` with new cue strips; returns the new strips. |
| `selected_caption_range(editor)` | 171 | Frame span of the selected caption strips, or None when none is selected. |
| `read_cues(scene, editor, channel, only_ours)` | 179 | Text strips on `channel` as (start_s, end_s, text) from frame 0, sorted by time. |
| `write_cues_file(path, cues, style, source)` | 202 | Save (start, end, text) captions as a cues JSON v1 the engine can export or render. |

### blender_addon/legendaria/timecode.py — 46 lines
Frames ↔ seconds and SRT/VTT text. Pure Python (no bpy), so it can be unit-tested.

| Function / class | Line | What it does |
|---|---|---|
| `seconds_to_frame(seconds, fps, offset)` | 11 | Frame number for a time in seconds, counted from `offset` (the media's first frame). |
| `frame_to_seconds(frame, fps, offset)` | 16 | Seconds from `offset` to `frame`. |
| `format_timestamp(seconds, separator)` | 21 | `HH:MM:SS,mmm` (SRT) or `HH:MM:SS.mmm` (VTT). Hours keep counting past 24. |
| `to_srt(cues)` | 30 | SRT text from (start, end, text) tuples. |
| `to_vtt(cues)` | 39 | WebVTT text from (start, end, text) tuples. |

### tools/project_map.py — 82 lines
Print the "File map" entries of docs/PROJECT.md for Python files.

| Function / class | Line | What it does |
|---|---|---|
| `first_line(node)` | 17 | First line of a node's docstring, or "". |
| `signature(fn)` | 27 | Compact `name(arg, ...)` without self/cls. |
| `rows(tree)` | 38 | (name, line, summary) for top-level functions, classes and public methods. |
| `describe(path)` | 56 | Markdown section for one file. |
| `main(argv)` | 72 | Print the sections for the given paths. |

### assets/brand/source/generate_brand_svgs.py — 73 lines
Generate the Legendária brand SVGs.

| Function / class | Line | What it does |
|---|---|---|
| `group(stroke, width)` | 23 | Wrap the symbol strokes in a <g> with the given stroke paint and width. |
| `write(name, body, vb, w, h, title)` | 28 | Write one SVG with viewBox, title and accessible label. |
| `lockup(name, font, weight, fill, bg)` | 62 | Symbol + "Legendária" wordmark (text; convert to paths afterwards). |

### assets/brand/source/generate_hero.py — 152 lines
Generate the glowing Legendária key art (hero and banner) as SVG.

| Function / class | Line | What it does |
|---|---|---|
| `symbol(x, y, width)` | 70 | Glowing symbol placed so its stroke box starts at (x, y) with the given width. |
| `background(w, h)` | 95 | Dark radial background with faint diagonal shapes and bands. |
| `text(x, y, size, anchor, tagline, tag_size, tag_dy)` | 107 | Montserrat wordmark with glow plus the spaced tagline. |
| `cover(lang)` | 115 | 1280x640 social preview: glowing symbol, wordmark, tagline, pitch lines and repo link. |
| `svg(w, h, body)` | 130 | Wrap a body in <svg> with defs, title and label. |


## 7. In progress

- **Now: plan 07 (web editor), phase 2.** Steps 31–33 cover the whole MVP list and the owner's first corrections (step 33): project file (ADR-016), cut + burn export, `flosub serve`, transcribe, JASSUB live preview, cue list, undo, autosave, timeline with waveform / drag / snap / zoom, glossary review, en + pt-BR, Playwright smoke in CI. **Next: the owner's manual test of the MVP**, then the owner's list of changes. Known gaps: font lookup is Linux-only (fontconfig), no `.ass`/`.srt` import, "add to glossary" from a selected word, mobile polish (touch drag on the timeline is untested), a recent-files list. Earlier: phase 0 spikes (step 29), Svelte (ADR-015), OpenReel dissection (step 30). ADR-014: the Blender add-on is frozen.
- Plan 02 (Blender add-on): done (steps 09–12).
- **Plan 03, accuracy:** done — 3a glossary (step 18), 3b LLM reviewer (step 19, experimental), glossary library (step 20), 3c Blender UI (step 22). Engine 0.1.0.dev4 is not on PyPI yet (needs the owner's tag), so "Install engine" gets it only after that release.
- **Plan 04, MVP subset (§10):** done in step 23: `.ass` export with the approved pop look, `flosub burn`, `flosub overlay`, and in Blender "Export ASS" and "Exact preview".
- **Pending owner decisions (agents: remind the owner after the MVP test round):** plan 04 §11.3. They are: the default preview in Blender (strips vs exact preview), import `.ass`/`.srt` + `flosub align --srt`, and the storage format (own JSON / `.ass` / extended `.ass`, plan 04 §11.5). Planned after the test feedback: Blender 5.2 minimum (ADR-013) and the native pop on word strips (pop by `font_size`, decided: plan 04 §11.4). Future idea kept: a full web subtitle editor (plan 05, last section).
- **Next:** the owner's manual test of the whole MVP, then the README, an alpha release and PyPI (the tag needs the owner's approval).
- Then plan 04 (CapCut animations — MVP look "one-word pop" decided, §8; style catalog §9 — `.ass` export / exact preview / burn-in / SRT alignment — §6), plan 05 (local API + `flosub gui` web interface).
- Plan 06 (Blender UX, draft): the owner finds the VSE hard to reach; one-click setup and entry points.
- **Known issues:** `dev-docs/known-issues.md` (KI-001, high: desktop freeze when loading `medium` from Blender).
- Backlog: plan 01, section 8.
