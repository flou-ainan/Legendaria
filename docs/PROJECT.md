# Project Map — Legendária

> A condensed map of the project, so agents and people can find what they need without rereading the code.
> **Update this file with every change to the project** (files, functions, stack, structure). Conventions: `docs/dev-docs/README.md`.

**Last updated:** 2026-10-24 — step 09 (engine cues: captions/subtitles styles; plan 02).

---

## 1. Overview

**Legendária** ("free subtitles, CapCut style") is a free, open-source automatic subtitle creator, inspired by CapCut's auto captions. Names (ADR-009): product **Legendária**; repository, Python package and add-on id `legendaria`; CLI command `flosub`.

What it does:

- Transcribes the audio locally on the GPU, with per-word timings.
- Turns the result into **editable text strips in Blender's Video Sequence Editor**.
- Exports SRT/VTT, or renders the video with the subtitles burned in.

Goals: a "next → next → finish" install for end users; a hackable setup driven by JSON configs; friendly to contributors; Linux, macOS and Windows 10+; UI and user docs in English and pt-BR (open to more languages).

**Current state:** the engine (`engine/`, CLI `flosub`) works: GPU/CPU transcription with word timings, JSON/SRT/VTT output, model download, layered JSON config, 32 tests. The Blender add-on (stage 2) is next. Plan: `dev-docs/planning/plan_01_mvp_engine_blender.md`.

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
| Editor | Blender 4.2+ Video Sequence Editor (`bpy`), extension format |
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
| [002](dev-docs/decisions/ADR-002-blender-vse-editor.md) | Blender VSE (4.2+) as the interactive editor | accepted |
| [003](dev-docs/decisions/ADR-003-engine-external-process.md) | Engine as an external process in its own venv, JSON contract | accepted |
| [004](dev-docs/decisions/ADR-004-dual-licensing.md) | Engine MIT, add-on GPL-3.0-or-later | accepted |
| [005](dev-docs/decisions/ADR-005-language-policy.md) | English dev content; user content in en + pt_BR, open to more | accepted |
| [006](dev-docs/decisions/ADR-006-json-configuration.md) | Layered JSON config files with JSON Schema | accepted |
| [007](dev-docs/decisions/ADR-007-cross-platform.md) | Linux, macOS, Windows 10+ | accepted |
| [008](dev-docs/decisions/ADR-008-contribution-workflow.md) | Branch + PR, Conventional Commits, SemVer, CI on 3 OSes | accepted |
| [009](dev-docs/decisions/ADR-009-project-name.md) | Name: Legendária (`legendaria`), CLI `flosub` | accepted |

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
│   ├── legendaria_engine/   # the package (see file map)
│   │   └── defaults/        # config.json (engine defaults), models.json (model catalog)
│   ├── schemas/             # JSON Schemas: config, models, transcript (editor autocomplete)
│   └── tests/               # pytest suite (no GPU or network needed)
├── tools/
│   └── project_map.py       # prints the "File map" entries below from the source
├── .github/
│   ├── workflows/ci.yml     # pre-commit + engine tests on Linux/macOS/Windows; aggregate `ci` check
│   ├── workflows/release.yml  # on tag vX.Y.Z: test, build, publish the engine to PyPI (Trusted Publishing, env `pypi`)
│   ├── ISSUE_TEMPLATE/      # bug, feature, translation forms + links to Discussions / security
│   └── pull_request_template.md
├── assets/
│   └── brand/           # brand kit: glowing key art (banner/hero/cover per language), flat symbol/icons/lockups, PNGs, favicon
└── docs/
    ├── PROJECT.md           # this file
    └── dev-docs/
        ├── README.md        # documentation conventions
        ├── planning/        # plans (before implementing)
        ├── devlog/          # executed steps
        ├── decisions/       # ADRs
        └── references/      # origin_brainstorm.md
```

The target layout for `blender_addon/` is in plan 01, section 4.3.

User files at runtime (per OS, via `platformdirs`; overridable with `LEGENDARIA_CONFIG_DIR` / `LEGENDARIA_DATA_DIR`):
- config dir (`~/.config/legendaria` on Linux): `config.json`, `models.json` (user overrides)
- data dir (`~/.local/share/legendaria` on Linux): `models/<name>/` (downloaded CTranslate2 models)

## 6. File map

Generated with `python3 tools/project_map.py <files>` and then reviewed. Regenerate it whenever code changes.

**Data files:**
- `engine/legendaria_engine/defaults/config.json`: engine defaults (model `small`, language `auto`, device `auto`, compute types, beam size, VAD, word timestamps, default `style`, cue `styles` (`subtitles`: film-style, up to 84 chars / 6 s, 2 lines of 42; `captions`: CapCut-style, up to 4 words / 22 chars / 2.2 s), output formats, UI language list).
- `engine/legendaria_engine/defaults/models.json`: model catalog (tiny, base, small, medium, large-v3, large-v3-turbo) with HF repo, size, VRAM, notes.
- `engine/schemas/*.schema.json`: JSON Schemas for config (incl. styles), models, transcript v1 and cues v1.
- `engine/tests/`: `conftest.py` (isolated dirs, sample transcript), `test_cues.py` (chunking rules), `test_formats.py`, `test_schema.py`, `test_config.py`, `test_cli.py`, `test_transcriber.py` (GPU→CPU fallback with a fake run). 51 tests.

**Outputs of `flosub transcribe` / `export`:** `<name>.json` (transcript v1: segments + word timings, the source of truth), `<name>.cues.json` (cues v1 in one style), `<name>.srt` / `.vtt` (from the cues). `export` re-chunks a saved transcript in any style without transcribing again.

**Progress event protocol** (stdout, one JSON object per line, `--progress json`):
- `start`: model, device, compute_type, language, duration.
- `progress`: `t`, `total` (in seconds).
- `model_download`: downloaded / total bytes, or `finished`.
- `log`, `warning`, `error`: carry `message`.
- `done`: `outputs` plus counts.

A `warning` followed by a new `start` means the run restarted on the CPU.

### engine/legendaria_engine/__init__.py — 3 lines
Legendária transcription engine.

### engine/legendaria_engine/__main__.py — 5 lines
Allow `python -m legendaria_engine`.

### engine/legendaria_engine/cli.py — 228 lines
`flosub` command line: transcribe, export, models, config.

| Function / class | Line | What it does |
|---|---|---|
| `output_path(stem, fmt)` | 18 | `<stem>.<fmt>`, or `<stem>.cues.json`; dots in the stem are kept (`a.b.mp4` → `a.b.srt`). |
| `write_outputs(transcript, stem, formats, config, style)` | 24 | Write the requested formats next to `stem` (no extension); returns the paths. |
| `check_style(config, style)` | 47 | The style to use: `--style` if given, else the config default; must exist. |
| `parse_formats(value)` | 55 | argparse type: comma-separated format list, validated against FORMATS. |
| `cmd_transcribe(args, reporter)` | 66 | `flosub transcribe`: resolve config and model, transcribe, write the outputs. |
| `cmd_export(args, reporter)` | 110 | `flosub export`: turn a transcript JSON into cues / SRT / VTT in a given style. |
| `cmd_models(args, reporter)` | 123 | `flosub models list|download`. |
| `cmd_config(args, reporter)` | 150 | `flosub config show|path`. |
| `build_parser()` | 159 | The argparse tree for all subcommands. |
| `main(argv)` | 208 | Entry point: run a subcommand and turn every failure into an `error` event. |

### engine/legendaria_engine/config.py — 109 lines
Layered JSON configuration: shipped defaults → user file → command-line values.

| Function / class | Line | What it does |
|---|---|---|
| `class ConfigError` | 22 | A config file is malformed or holds an invalid value. |
| `read_json(path)` | 26 | Read a JSON object from a file, dropping `$schema`; raise ConfigError on bad JSON. |
| `deep_merge(base, override)` | 38 | Return `base` updated with `override`; nested objects are merged key by key. |
| `validate(config, source)` | 49 | Check the values the engine relies on, with errors that name the bad key. |
| `load_config(overrides)` | 88 | Defaults, then the user's `config.json` if present, then non-None `overrides`. |
| `load_models()` | 100 | The model catalog: shipped `models.json` plus the user's additions or changes. |

### engine/legendaria_engine/cuda_libs.py — 56 lines
Make the NVIDIA libraries installed by pip (cuBLAS, cuDNN) visible to CTranslate2.

| Function / class | Line | What it does |
|---|---|---|
| `nvidia_lib_dirs()` | 18 | Library folders of the installed `nvidia.*` packages (empty when not installed). |
| `ensure_cuda_libs()` | 33 | Expose the NVIDIA libraries to the current process. Call before importing ctranslate2. |

### engine/legendaria_engine/cues.py — 124 lines
Cues: the timed text blocks shown on screen, built from word timings by a style.

| Function / class | Line | What it does |
|---|---|---|
| `class Cue` | 20 | One block of text on screen, with the words it contains. |
| `class CueList` | 30 | Cues for one media file in one style (cues JSON v1). |
| `CueList.to_dict()` | 39 | Plain dict ready for JSON. |
| `CueList.save(path)` | 43 | Write as pretty UTF-8 JSON. |
| `_join(words)` | 48 | Concatenate words as Whisper spells them: a leading space marks a new word, |
| `_ends_with(word, chars)` | 54 |  |
| `make_cues(transcript, style, style_name)` | 59 | Chunk the transcript's words into cues that respect the style's limits. |
| `_apply_min_duration(cues, min_duration)` | 107 | Stretch cues shorter than `min_duration`, without overlapping the next cue. |
| `wrap_lines(text, line_length)` | 117 | Split text into two balanced lines when it is longer than `line_length`. |

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
Subtitle writers: cues → SRT / VTT text.

| Function / class | Line | What it does |
|---|---|---|
| `format_timestamp(seconds, separator)` | 10 | `HH:MM:SS,mmm` (SRT) or `HH:MM:SS.mmm` (VTT). Hours keep counting past 24. |
| `to_srt(cues, line_length)` | 19 | Numbered SRT blocks, one per cue; long cues wrap into two lines. |
| `to_vtt(cues, line_length)` | 28 | WebVTT blocks, one per cue; long cues wrap into two lines. |

### engine/legendaria_engine/models.py — 105 lines
List, download and locate Whisper models (stored in the per-OS data dir).

| Function / class | Line | What it does |
|---|---|---|
| `model_path(name)` | 23 | Folder where a catalog model is (or will be) stored. |
| `is_installed(name)` | 28 | True when the model folder has all the files CTranslate2 needs. |
| `list_models()` | 34 | Catalog entries with an `installed` flag, in catalog order. |
| `_progress_class(reporter, name, expected_bytes)` | 42 | A tqdm-compatible class that turns Hugging Face download progress into events. |
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

### engine/legendaria_engine/schema.py — 79 lines
Transcript format (JSON v1): the contract between the engine and the Blender add-on.

| Function / class | Line | What it does |
|---|---|---|
| `class Word` | 14 | One recognized word with its timing (seconds) and confidence. |
| `class Segment` | 24 | A sentence-like chunk of speech; becomes one subtitle cue. |
| `class Transcript` | 34 | The whole transcription of one media file (JSON v1). |
| `Transcript.to_dict()` | 46 | Plain dict ready for JSON. |
| `Transcript.from_dict(data)` | 51 | Build from a dict, rejecting other schema versions. |
| `Transcript.save(path)` | 72 | Write as pretty UTF-8 JSON. |
| `Transcript.load(path)` | 77 | Read a transcript JSON file. |

### engine/legendaria_engine/transcriber.py — 133 lines
Speech-to-text. A small backend interface keeps room for other engines (e.g. Apple Silicon).

| Function / class | Line | What it does |
|---|---|---|
| `class Options` | 14 | Everything a backend needs to run one transcription. |
| `class Backend` | 27 | Interface for speech-to-text engines (faster-whisper today; Apple Silicon later). |
| `Backend.transcribe(media, options, reporter)` | 32 | Transcribe `media`, reporting progress, and return the transcript. |
| `cuda_available()` | 37 | True when CTranslate2 sees at least one CUDA device. |
| `class FasterWhisperBackend` | 47 | faster-whisper (CTranslate2): CUDA on NVIDIA GPUs, int8 on CPU. |
| `FasterWhisperBackend.transcribe(media, options, reporter)` | 57 | Try each device in turn; in `auto` mode a GPU failure falls back to the CPU. |
| `get_backend(name)` | 129 | Instantiate a backend by name. |


### tools/project_map.py — 80 lines
Print the "File map" entries of docs/PROJECT.md for Python files.

| Function / class | Line | What it does |
|---|---|---|
| `first_line(node)` | 17 | First line of a node's docstring, or "". |
| `signature(fn)` | 27 | Compact `name(arg, ...)` without self/cls. |
| `rows(tree)` | 38 | (name, line, summary) for top-level functions, classes and public methods. |
| `describe(path)` | 54 | Markdown section for one file. |
| `main(argv)` | 70 | Print the sections for the given paths. |

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

- Plan 01 approved, with no open questions left. `main` is protected: every change goes through a PR (ADR-008).
- Brand kit in `assets/brand/` (Montserrat; glowing banner at the top of both READMEs).
- Stage 0 (project foundation) done.
- Stage 1 (engine) done; `legendaria` 0.1.0.dev0 published on PyPI (name reserved).
- Next: stage 2 (Blender add-on).
