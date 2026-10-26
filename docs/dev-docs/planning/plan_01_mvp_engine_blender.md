# Plan 01 — MVP: transcription engine + Blender add-on, and the product roadmap

**Status:** approved
**Date:** 2026-10-23 (revised 2026-10-24)
**Origin:** `references/origin_brainstorm.md`
**Related decisions:** ADR-001 to ADR-009

## 1. Vision

**Legendária** ("free subtitles, CapCut style"; CLI `flosub`) is a free, open-source automatic subtitle creator, in the spirit of CapCut's auto captions:

- **For end users:** install with a "next → next → finish" installer, open Blender, drop a video in, click one button, and get editable, stylable subtitles. No terminal, no Python, no CUDA setup.
- **For contributors:** clear docs, small modules, tests, and behavior driven by JSON config files, so most tweaks never touch code.
- **Everywhere:** Linux, macOS, and Windows 10+.
- **In your language:** English as the source language, Brazilian Portuguese always maintained, and other languages open to contributors. This covers the UI, the README, and the user docs.

## 2. Product principles (they apply to every phase)

| Principle | What it means in practice |
|---|---|
| Easy to access | One installer per OS, models downloaded from inside the UI, sensible defaults (`small` model, auto language), errors that say how to fix the problem |
| Cross-platform from day one | `pathlib` everywhere; `subprocess` with argument lists, never shell strings; per-OS user dirs via `platformdirs`; venv layout differences (`bin/` vs `Scripts/`) isolated in one helper; CI on all three OSes |
| Hackable | Defaults, models, subtitle splitting rules, style presets and translations live in JSON files. The user can override them in a per-user config dir without editing the installed files. A JSON Schema is published for each file, so editors autocomplete it (ADR-006) |
| Bilingual | Dev content in English. User content in English plus `pt_BR`, with a structure that accepts more languages (ADR-005) |
| Offline and private | After a model is downloaded, everything runs locally. No telemetry |
| Clear licensing | Engine MIT, Blender add-on GPL-3.0-or-later (ADR-004) |

## 3. Roadmap

| Phase | Content | Platforms | Distance |
|---|---|---|---|
| **0. Foundation** | Contribution workflow, CI, templates, final name + logo (section 7) | all (CI) | **now** |
| **1. MVP** | Engine CLI + Blender add-on: transcribe pt/en, text strips, SRT/VTT export, model download, "Install engine" button, pt_BR/en UI | Linux (NVIDIA + CPU), code already portable | next |
| 2a. Accuracy (plan 03) | Glossary (Whisper bias + deterministic fixes) and LLM reviewer (local OpenAI-compatible, cloud optional) as suggestions; device profiles | all | **next** |
| 2b. CapCut styles (plan 04) | Animations (pop-in, current-word highlight), style presets (JSON), burn-in through Blender render | Linux | after plan 03 |
| 2c. Local API + web GUI (plan 05) | `flosub gui` in the browser, HTTP API for all clients; native window (pywebview) optional after MVP | all | after plan 04 |
| 3. Cross-platform | Windows (CUDA + CPU) and macOS (CPU; Apple Silicon backend open to contributors) | all | later |
| 4. Easy install | Native per-OS installers wrapping the "Install engine" flow, optionally bundling a portable Blender | all | later |
| 5. User docs and outreach | MkDocs Material site on GitHub Pages (en + pt-BR), YouTube tutorial | — | later |
| Out of scope for now | Mobile app (whisper.cpp / React Native), cloud API | — | future plan |

Phases 3–5 are far from the MVP, but the MVP must not block them. The constraints they impose are listed in section 5.

## 4. Phase 1 — MVP in detail

### 4.1 Context validated in the brainstorm

- **Ollama cannot run Whisper.** Community models fail with `unknown model architecture` (ADR-001).
- **faster-whisper on the GPU works:** 49 min of audio in about 38 s with the `base` model in fp16.
- **cuDNN:** CTranslate2 needs `libcudnn_ops.so.9`. The pip wheels install it under `site-packages/nvidia/cudnn/lib`, but the dynamic linker does not see it there, so the process aborts with a core dump.
- **`.ass` is not an editor:** it cannot be edited interactively. Blender's VSE gives visual editing plus Python scripting (ADR-002).
- **Blender's bundled Python lacks faster-whisper and CUDA.** The add-on runs the engine as an external process and exchanges JSON with it (ADR-003).

Environment checked on 2026-10-23: Blender 4.2.0 (correction 2026-10-24: only a dangling `~/.local/bin/blender` symlink existed; Blender 4.2.23 and 5.2.3 were installed portably for plan 02), Python 3.10.12, faster-whisper 1.2.1, ctranslate2 4.6.1, nvidia-cudnn-cu12 9.1, nvidia-cublas-cu12 12.1, ffmpeg 4.4.2, NVIDIA driver 595, RTX 2070 Super 8 GB.

### 4.2 Fixes over the brainstorm's sample code

| Problem in the sample code | How it is handled here |
|---|---|
| JSON keeps segments only and drops word timings | JSON keeps `words` with per-word timings, the base for CapCut-style captions |
| `subprocess.run` freezes Blender | Modal operator with a timer reads progress without blocking the UI; `Esc` cancels |
| Hardcoded paths (`/home/flou/...`, `python3.10`) | Engine location is resolved by the add-on (managed venv) or set in preferences |
| `LD_LIBRARY_PATH` in `.bashrc` | The engine finds the NVIDIA libs in its own venv and preloads them (Linux) or registers DLL dirs (Windows) |
| PyTorch installed only to get cuDNN | Not needed: faster-whisper does not use torch. `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` are enough |
| Export uses `frame_start` / `frame_end` | Uses `frame_final_start` / `frame_final_end`, which respect strip trims |
| `int()` when converting to frames | `round()`, so offsets do not accumulate |
| Timestamps formatted with `str(timedelta)` | A dedicated, tested function (hours > 24, correct milliseconds) |
| UI strings hardcoded in Portuguese | Every string goes through Blender's translation system, with locale JSON files |

### 4.3 Target layout

```
engine/                              # MIT — transcription engine, own venv
├── LICENSE                          # MIT (same as root)
├── pyproject.toml                   # package "legendaria", command `flosub`
├── legendaria_engine/
│   ├── __init__.py
│   ├── cli.py                       # argparse: transcribe / export / models / config
│   ├── config.py                    # loads defaults + user overrides + CLI flags
│   ├── paths.py                     # per-OS user dirs (config, models, cache)
│   ├── cuda_libs.py                 # locate and preload cuDNN/cuBLAS (Linux/Windows)
│   ├── models.py                    # list / download / verify Whisper models
│   ├── transcriber.py               # faster-whisper, GPU→CPU fallback, progress events
│   ├── events.py                    # JSON-lines progress protocol on stdout
│   ├── schema.py                    # transcript JSON v1
│   ├── formats.py                   # transcript → SRT / VTT
│   └── defaults/
│       ├── config.json              # default engine settings
│       └── models.json              # catalog: name, repo, size, VRAM, notes
├── schemas/                         # JSON Schemas published for editors
│   ├── config.schema.json
│   ├── models.schema.json
│   └── transcript.schema.json
└── tests/

blender_addon/legendaria/        # GPL-3.0-or-later — Blender 4.2+ extension
├── LICENSE                          # GPL-3.0-or-later
├── blender_manifest.toml
├── __init__.py                      # register / unregister
├── compat.py                        # VSE API differences across Blender versions
├── engine_bridge.py                 # find/launch engine, read progress events
├── i18n.py                          # loads locales/*.json into bpy.app.translations
├── preferences.py                   # engine path, model (with download), language, device
├── properties.py                    # scene props: channel, style preset
├── operators.py                     # transcribe (modal), export SRT/VTT, download model
├── strips.py                        # transcript → text strips; strips → cues
├── panel.py                         # "Subtitles" tab in the sequencer sidebar
├── locales/
│   ├── pt_BR.json                   # English msgid → Portuguese
│   └── README.md                    # how to add a language
└── presets/
    └── default.json                 # strip style (font size, position, shadow...)

README.md / README.pt-BR.md          # user-facing, bilingual
```

### 4.4 Stage 1 — Engine (`engine/`) — done (step 07)

As-built differences from the text below (see step 07):
- The NVIDIA libraries are an optional `cuda` extra, so CI and CPU/Mac installs stay small; the installer adds it when it finds an NVIDIA GPU.
- On Linux, `cuda_libs.py` re-executes the process once with `LD_LIBRARY_PATH` set; this is more reliable than preloading with `ctypes`.
- `--progress auto|json|human` is a global flag: human output when stdout is a terminal, JSON lines otherwise (so the add-on gets JSON without asking).
- In `auto` mode, a GPU failure during model loading *or* decoding retries the whole run on the CPU (`warning` event, then a new `start`).
- Users can add models through a user `models.json`; the test dirs are isolated with `LEGENDARIA_CONFIG_DIR` / `LEGENDARIA_DATA_DIR`.

- **Environment:** a dedicated venv (`engine/.venv` in development; in production, a managed venv in the user data dir, created by the installer or by the add-on, see phase 4). Dependencies: `faster-whisper`, `platformdirs`, `nvidia-cublas-cu12` and `nvidia-cudnn-cu12==9.*` (Linux/Windows only, through environment markers).
- **`cuda_libs.py`:** finds `nvidia/*/lib` (Linux) or `nvidia/*/bin` (Windows) inside the venv.
  - Linux: preloads the `.so` files with `ctypes` before importing `ctranslate2`; if that is not enough, it re-execs itself with `LD_LIBRARY_PATH` set.
  - Windows: uses `os.add_dll_directory`.
  - macOS: no-op.
- **`config.py`:** three layers, each one overriding the previous:
  1. `defaults/config.json` (shipped).
  2. User file in the per-OS config dir: `~/.config/legendaria/config.json`, `%APPDATA%\legendaria\config.json`, or `~/Library/Application Support/legendaria/config.json`.
  3. CLI flags.

  `flosub config show` prints the merged result and `flosub config path` prints where the user file goes.
- **`models.py` + `models.json`:** catalog of the Whisper models (`tiny` … `large-v3`, `large-v3-turbo`), each with size, approximate VRAM, and a recommendation. The default is `small`.
  - `flosub models list` shows the catalog and what is installed.
  - `flosub models download <name>` downloads a model with progress events.
  - Models are stored in the per-OS data dir, not in the HF cache, so the add-on can show and manage them.
  - Adding a model means adding an entry to `models.json`.
- **`transcriber.py`:**
  - `device="auto"` tries `cuda`/`float16`, then falls back to `cpu`/`int8` with a clear warning.
  - `word_timestamps=True`, plus `vad_filter=True` (configurable), which skips silences and reduces hallucinations.
  - Language: `auto` or a fixed code.
  - Video input works directly (faster-whisper decodes through PyAV), so no ffmpeg install is needed; to be confirmed during implementation.
- **`events.py`:** progress as one JSON object per line on stdout, for example `{"event":"progress","t":123.4,"total":2968.0}`. Other events: `log`, `warning`, `model_download`, `done`, `error`. The add-on parses these lines. With `--human`, the engine shows a tqdm bar instead.
- **`schema.py`**, transcript JSON v1:
  ```json
  {
    "version": 1,
    "source": "video.mp4",
    "language": "pt", "language_probability": 0.99,
    "duration": 2968.4, "model": "small", "device": "cuda",
    "segments": [
      {"start": 0.0, "end": 2.5, "text": "Hello, this is a test.",
       "words": [{"start": 0.0, "end": 0.4, "word": "Hello,", "probability": 0.98}]}
    ]
  }
  ```
- **`cli.py`:**
  - `flosub transcribe <file> [--model] [--language] [--device auto|cuda|cpu] [--output-dir] [--format json,srt,vtt] [--human]`
  - `flosub export <file.json> --format srt|vtt`
  - `flosub models list|download`
  - `flosub config show|path`
- **CLI language:** English only in the MVP, since the CLI is a power-user tool. The add-on translates whatever it shows to the user.
- **Tests (pytest):** timestamp formatting (0 s, 59.999 s, > 1 h, > 24 h), valid SRT/VTT output, schema round-trip, config layering, catalog validation against the JSON Schema. Real transcription is tested manually with a short clip.

### 4.5 Stage 2 — Blender add-on (`blender_addon/legendaria/`)

- **Compatibility:** Blender **4.2 and newer** (the extensions format starts at 4.2). `compat.py` isolates the VSE API changes, for example `sequence_editor.sequences` → `strips` in 4.4+ (the old API is removed in 5.0) and any renames to `new_effect` or the text strip properties. Manual testing covers 4.2 LTS and the latest stable release.
- **`engine_bridge.py`:** locates the engine, in this order:
  1. Path set in preferences.
  2. Managed venv in the user data dir.
  3. `flosub` on PATH.

  It runs the engine with `subprocess.Popen` (argument list, no shell, Windows-safe flags) and parses the progress events. If no engine is found, the panel shows a friendly "Engine not installed" box with instructions.
- **"Install engine" button** (preferences): downloads `uv` for the current OS, runs `uv venv --python 3.11` in the per-OS data dir, installs `legendaria` into it, and downloads the `small` model. Progress and errors appear in the UI. A "Repair / reinstall" action reruns the same steps. In the MVP the engine is installed from the git repository; later, from PyPI.
- **Preferences:** engine path; model dropdown fed by `flosub models list`, with a **Download** button and a progress bar; language (auto / pt / en / ...); device.
- **"Generate subtitles" operator** (modal):
  1. Takes the active `MOVIE` or `SOUND` strip and resolves its path with `bpy.path.abspath`.
  2. Starts `flosub transcribe ... --format json`.
  3. A timer updates the progress bar and the status line. `Esc` cancels and kills the process.
  4. When the engine finishes, the add-on creates one text strip per segment on the chosen channel, using the style from `presets/default.json`. Positions account for the media strip start and any trim at its head (`frame_offset_start`).
- **"Export SRT/VTT" operator:**
  - Reads the text strips on the channel, sorted by `frame_final_start`, converts frames to seconds with the real fps (`fps / fps_base`), and writes the file next to the `.blend`, or to a path picked in a file dialog.
  - Uses the same timestamp formatting as the engine. The code is copied into `strips.py`, because the add-on cannot import the engine.
- **i18n:** every label, tooltip and message is written in English and translated through `bpy.app.translations`, with the dictionaries loaded from `locales/*.json`. Blender switches language from its own setting (Preferences → Interface → Language). `locales/README.md` explains how to add a language.
- **Panel:** a "Subtitles" tab in the sequencer sidebar with three blocks: setup, generate, export.

### 4.6 Definition of done (MVP)

- [x] `flosub transcribe video.mp4` produces JSON, SRT and VTT on the GPU, with no manual `export`.
- [x] Without a GPU, or with `--device cpu`, it runs on CPU.
- [ ] On a machine with no engine, "Install engine" in Blender leaves a working engine with the `small` model, with no terminal use.
- [ ] Portuguese and English clips both transcribe correctly with auto-detection and with a fixed language.
- [x] `flosub models download <name>` works and the model shows as installed (tested with `tiny`).
- [x] The user config file overrides a default (for example the model) with no code change.
- [x] Engine tests pass (`pytest engine/tests`): 32 tests, in CI on all three OSes.
- [ ] Blender 4.2 and the latest stable: select a video → Generate → strips appear on the right channel, aligned with the audio; the progress bar moves; the UI does not freeze.
- [ ] Editing a strip's text and timing, then exporting SRT, gives a file that reflects the edits.
- [ ] With Blender set to Portuguese, the add-on UI is in Portuguese.
- [ ] `PROJECT.md` lists every file with line counts and functions; there is one devlog step per stage.

## 5. Constraints that the later phases impose on the MVP

- **Cross-platform (phase 3):**
  - No POSIX-only code in the engine or the add-on.
  - The venv path helper handles `bin/` vs `Scripts/`, and `cuda_libs.py` already has a Windows branch.
  - On macOS, CTranslate2 has no GPU backend, so it runs on CPU. A second backend (for example `mlx-whisper` or whisper.cpp with Metal) could be added later behind a `backend` key in the config. The transcriber therefore has a small backend interface from the start.
- **Installer (phase 4):** the add-on must work with an engine installed outside the repository (the managed venv in the user data dir). Nothing may assume a dev checkout.
- **Docs site (phase 5):** user-facing docs are organized by language from the start (`docs/user/en/`, `docs/user/pt-BR/`), so a static site generator can publish them directly.
- **i18n:** no user-visible string outside the translation layer, ever.

## 6. Decided

Round 1 (2026-10-24):

1. Engine environment: **dedicated venv**.
2. Default model: **`small`**, with in-app download of the others.
3. Licenses: **engine MIT, add-on GPL-3.0-or-later** (ADR-004).
4. Blender: **4.2 and newer**.
5. The real brainstorm stays local (gitignored). A generic version lives in `references/origin_brainstorm.md`.
6. Dev docs, code and comments in English. User-facing content in English plus pt-BR, open to other languages (ADR-005).
7. Hackable through layered JSON configs (ADR-006).
8. Cross-platform target: Linux, macOS, Windows 10+ (ADR-007).

Round 2 (2026-10-24):

9. **Installer:**
   - First, option (a): the user installs the add-on zip, then clicks **"Install engine"** in the add-on preferences. The add-on downloads `uv`, creates the managed venv with the pinned Python, installs the engine and fetches the `small` model, all with a progress bar.
   - Later, for less technical users: (b) a native installer per OS that wraps (a), and/or (c) the same plus a portable Blender with the add-on preinstalled. Both live in phase 4.
10. **macOS:** CPU only (int8), which is already acceptable: it was tested on a Ryzen CPU. An Apple Silicon backend (`mlx-whisper`, or whisper.cpp with Metal) is left open for a contributor with a Mac, tracked as a "help wanted" issue. The backend interface in `transcriber.py` exists so that PR stays small.
11. **Docs site:** MkDocs Material, published on GitHub Pages, with `docs/user/en/` and `docs/user/pt-BR/` (phase 5).
12. **Transcription languages in the MVP:** **Portuguese and English** are first-class:
    - The language selector offers auto / pt / en, and the full Whisper language list is configurable through JSON.
    - Both languages are tested on real clips before the MVP is done.
    - Translation (for example pt speech → en subtitles) is not in the MVP (open question 9).
13. **Burn-in:** only through Blender's render in phase 2. The fast path (generate `.ass` and burn with FFmpeg/NVENC, no editor) goes to the backlog (section 8).
14. **Python:** pinned (3.11) and installed by `uv` into the managed venv, independent of the system Python. This is still a venv: `uv` just creates it with a known Python version, so every user on every OS runs the same thing.
15. **Contribution workflow:** the lightweight standard used by serious open-source projects (ADR-008, stage 0 below).

Round 3 (2026-10-24):

16. **Name (ADR-009):** the product is **Legendária**. The repository, the Python package (`legendaria`, import `legendaria_engine`) and the add-on id are `legendaria`, and the CLI command is **`flosub`**. Slogan: "free subtitles, CapCut style" / "legendas livres, estilo CapCut".
17. **Translation:** not planned. It stays in the backlog until the owner revisits it.
18. **`main` protection:** enabled. PRs are required, also for admins; linear history; no force-push or deletion; squash merge only; branches are deleted after merge. The required CI check is added when the CI workflow exists (stage 0).

## 7. Stage 0 — Project foundation (before the engine)

Following ADR-008:

- [x] `CONTRIBUTING.md` (English), linked from both READMEs. It covers how to set up, run tests, branch, commit and open a PR, plus a "your first contribution" section and how to add a translation.
- [x] `CODE_OF_CONDUCT.md` (Contributor Covenant 2.0, as provided by GitHub).
- [x] `SECURITY.md`; GitHub private vulnerability reporting enabled.
- [x] `CHANGELOG.md` (Keep a Changelog format) and versioning with SemVer, starting at `0.1.0`.
- [x] `.github/ISSUE_TEMPLATE/` (bug report, feature request, translation) and `.github/pull_request_template.md`. The PR template includes "docs updated (devlog / PROJECT.md)".
- [x] `ruff` (lint and format) and `pre-commit` config, plus `.editorconfig` and `.gitattributes` (LF line endings). `pytest` is wired in once the engine exists.
- [x] GitHub Actions CI: pre-commit (ruff) and, once the engine exists, pytest on Linux, macOS and Windows, with one aggregate `ci` check.
- [x] Protect `main` (PR required, squash only, `ci` check required).
- [x] GitHub repository settings: labels `good first issue`, `help wanted`, `translation`; enable Discussions.
- [x] Final project name applied everywhere (Legendária / `flosub`).
- [x] Logo: brand kit in `assets/brand/` (step 05).

## 8. Backlog (not scheduled)

- ~~Fast burn-in without the editor~~: moved into plan 04 §6 (`flosub burn`, `.ass` + FFmpeg/libass).
- Apple Silicon backend (contributor-led).
- Subtitle translation (Whisper translate mode, or an LLM pass).
- WhisperX-style forced alignment, if word timings are not precise enough (fallback for plan 04 §6.4 `flosub align`).
- Mobile app and cloud API (from the origin brainstorm).
- Kdenlive integration (the owner edits in Kdenlive): use the CLI or the local API (ADR-011).
- Native window for `flosub gui` (pywebview), after the MVP (plan 05).
- Refine the glowing key art (more sparkle/flare, closer to the Gemini reference). The owner considers the current version good for now.

## 9. Open questions

1. ~~Installer strategy~~: decided (9).
2. ~~macOS acceleration~~: decided (10).
3. ~~Docs site tool~~: decided (11).
4. ~~Transcription languages~~: decided (12).
5. ~~Burn-in~~: decided (13).
6. ~~Name~~: decided (16, ADR-009).
7. ~~Contribution workflow~~: decided (15, ADR-008).
8. ~~Python~~: decided (14).
9. ~~Translation~~: decided (17), backlog.

No open questions remain.
