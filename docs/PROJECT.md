# Project Map — Legendária

> A condensed map of the project, so agents and people can find what they need without rereading the code.
> **Update this file with every change to the project** (files, functions, stack, structure). Conventions: `docs/dev-docs/README.md`.

**Last updated:** 2026-10-26 — step 18 (plan 03 stage 3a: glossary, Whisper hotwords, deterministic fixes, review suggestions; engine 0.1.0.dev4).

---

## 1. Overview

**Legendária** ("free subtitles, CapCut style") is a free, open-source automatic subtitle creator, inspired by CapCut's auto captions. Names (ADR-009): product **Legendária**; repository, Python package and add-on id `legendaria`; CLI command `flosub`.

What it does:

- Transcribes the audio locally on the GPU, with per-word timings.
- Turns the result into **editable text strips in Blender's Video Sequence Editor**.
- Exports SRT/VTT, or renders the video with the subtitles burned in.

Goals: a "next → next → finish" install for end users; a hackable setup driven by JSON configs; friendly to contributors; Linux, macOS and Windows 10+; UI and user docs in English and pt-BR (open to more languages).

**Current state:** the engine (`flosub`, on PyPI as `legendaria`) and the Blender add-on core work end to end: select a video in the VSE, pick a model (auto-download), generate CapCut-style caption strips in the background, confirm before replacing, re-apply a style, export SRT/VTT, English/Portuguese UI. "Install engine" sets everything up from Blender (2b); "Regenerate range" redoes only the preview range or the selected captions (2c). Plan 02 is complete; next is plan 03 (CapCut animations and style presets). Plans: `dev-docs/planning/plan_01_*`, `plan_02_blender_addon.md`.

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
| [010](dev-docs/decisions/ADR-010-review-pipeline.md) | Glossary in 3 layers + LLM reviewer (OpenAI-compatible, suggestions), device profiles | accepted |
| [011](dev-docs/decisions/ADR-011-modular-architecture.md) | Engine core → CLI/HTTP API → clients (Blender, web GUI, Kdenlive later) | accepted |
| [012](dev-docs/decisions/ADR-012-ass-styled-format.md) | `.ass` as styled format: one preset → `.ass` (libass overlay/burn) and Blender strips | proposed |

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
├── tools/
│   └── project_map.py       # prints the "File map" entries below from the source
├── .github/
│   ├── workflows/ci.yml     # pre-commit, engine + add-on tests on Linux/macOS/Windows; add-on smoke test inside Blender 4.2.23 and 5.2.3; aggregate `ci` check
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
        ├── known-issues.md  # problems seen in real use, with evidence and how to investigate
        └── references/      # origin_brainstorm.md, ass_brainstorm.md
```

Build the add-on package: `blender --command extension build --source-dir blender_addon/legendaria --output-dir dist` (gives `legendaria-<version>.zip`, installed with Edit → Preferences → Get Extensions → Install from Disk).

User files at runtime (per OS, via `platformdirs`; overridable with `LEGENDARIA_CONFIG_DIR` / `LEGENDARIA_DATA_DIR`):
- data dir `engine/` (only when installed from Blender): `uv/`, `python/` (uv-managed 3.11), `venv/` (flosub). Deleting it uninstalls.
- config dir (`~/.config/legendaria` on Linux): `config.json`, `models.json` (user overrides)
- data dir (`~/.local/share/legendaria` on Linux): `models/<name>/` (downloaded CTranslate2 models)

## 6. File map

Generated with `python3 tools/project_map.py <files>` and then reviewed. Regenerate it whenever code changes.

**Data files:**
- `engine/legendaria_engine/defaults/config.json`: engine defaults (`review`: mode suggest/auto, glossary_bias, fuzzy_threshold 0.82, low_confidence 0.5; model `small`, language `auto`, device `auto`, compute types, beam size, VAD, word timestamps, default `style`, cue `styles` (`pop`: one word at a time, two when the first has ≤ 3 letters, glued pieces like "-vindas" kept, gaps ≤ 0.35 s filled — the MVP default in Blender; `captions`: up to 4 words / 22 chars / 2.2 s; `subtitles`: film-style, up to 84 chars / 6 s, 2 lines of 42), output formats, UI language list).
- `engine/legendaria_engine/defaults/models.json`: model catalog (tiny, base, small, medium, large-v3, large-v3-turbo) with HF repo, size, VRAM, notes.
- `engine/schemas/*.schema.json`: JSON Schemas for config (incl. styles), models, transcript v1 and cues v1.
- `engine/tests/`: `conftest.py` (isolated dirs, sample transcript), `test_cues.py` (chunking rules), `test_formats.py`, `test_schema.py`, `test_config.py`, `test_cli.py`, `test_transcriber.py` (GPU→CPU fallback with a fake run), `test_glossary.py`, `test_fix_rules.py`. 76 tests.

**Glossary and review (plan 03, stage 3a):** glossary files are plain text (`Term` or `wrong -> right`): global `<config dir>/glossary.txt`, project `legendaria-glossary.txt` next to the media or transcript, and `--glossary FILE`. `transcribe` passes the terms to Whisper as `hotwords` (layer 1). `flosub review FILE.json` (or `transcribe --review`) finds explicit fixes and fuzzy matches of uncertain words (layer 2) and writes `<name>.review.json` (mode `suggest`) or applies them (`auto`). `flosub review apply FILE.review.json --ids …|--all [--format srt]` applies the chosen ones, re-timing the words. `flosub glossary path|show|add` is the base of every UI's "Add to glossary".

**Range regeneration:** `flosub transcribe media --clip START,END --update saved.json` transcribes only that range and merges it into the saved transcript word by word (`Transcript.merged_with`), so nothing is duplicated or lost at the boundaries.

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

### engine/legendaria_engine/cli.py — 433 lines
`flosub` command line: transcribe, export, models, config.

| Function / class | Line | What it does |
|---|---|---|
| `output_path(stem, fmt)` | 18 | `<stem>.<fmt>`, or `<stem>.cues.json`; dots in the stem are kept (`a.b.mp4` → `a.b.srt`). |
| `write_outputs(transcript, stem, formats, config, style)` | 24 | Write the requested formats next to `stem` (no extension); returns the paths. |
| `parse_clip(value)` | 47 | `START,END` in seconds → (start, end); raises ValueError on bad input. |
| `check_style(config, style)` | 58 | The style to use: `--style` if given, else the config default; must exist. |
| `parse_formats(value)` | 66 | argparse type: comma-separated format list, validated against FORMATS. |
| `cmd_transcribe(args, reporter)` | 77 | `flosub transcribe`: resolve config and model, transcribe, write the outputs. |
| `load_glossary(args, media, reporter)` | 144 | Global + project (next to `media`) + `--glossary` files, unless `--no-glossary`. |
| `run_review(transcript, glossary, config, stem, reporter)` | 157 | Layer 2 fixes: write `<stem>.review.json` (suggest) or apply them (auto). |
| `cmd_export(args, reporter)` | 182 | `flosub export`: turn a transcript JSON into cues / SRT / VTT in a given style. |
| `cmd_review(args, reporter)` | 195 | `flosub review FILE.json` (suggest or auto) and `flosub review apply FILE.review.json`. |
| `review_apply(path, args, reporter)` | 221 | Apply accepted suggestions (`--ids`, or every pending one with `--all`) to the transcript. |
| `cmd_glossary(args, reporter)` | 255 | `flosub glossary path|show|add` (global by default, or the project of --media). |
| `cmd_models(args, reporter)` | 291 | `flosub models list|download`. |
| `cmd_config(args, reporter)` | 318 | `flosub config show|path`. |
| `build_parser()` | 327 | The argparse tree for all subcommands. |
| `main(argv)` | 413 | Entry point: run a subcommand and turn every failure into an `error` event. |

### engine/legendaria_engine/config.py — 117 lines
Layered JSON configuration: shipped defaults → user file → command-line values.

| Function / class | Line | What it does |
|---|---|---|
| `class ConfigError` | 24 | A config file is malformed or holds an invalid value. |
| `read_json(path)` | 28 | Read a JSON object from a file, dropping `$schema`; raise ConfigError on bad JSON. |
| `deep_merge(base, override)` | 40 | Return `base` updated with `override`; nested objects are merged key by key. |
| `validate(config, source)` | 51 | Check the values the engine relies on, with errors that name the bad key. |
| `load_config(overrides)` | 96 | Defaults, then the user's `config.json` if present, then non-None `overrides`. |
| `load_models()` | 108 | The model catalog: shipped `models.json` plus the user's additions or changes. |

### engine/legendaria_engine/cuda_libs.py — 56 lines
Make the NVIDIA libraries installed by pip (cuBLAS, cuDNN) visible to CTranslate2.

| Function / class | Line | What it does |
|---|---|---|
| `nvidia_lib_dirs()` | 18 | Library folders of the installed `nvidia.*` packages (empty when not installed). |
| `ensure_cuda_libs()` | 33 | Expose the NVIDIA libraries to the current process. Call before importing ctranslate2. |

### engine/legendaria_engine/cues.py — 168 lines
Cues: the timed text blocks shown on screen, built from word timings by a style.

| Function / class | Line | What it does |
|---|---|---|
| `class Cue` | 21 | One block of text on screen, with the words it contains. |
| `class CueList` | 31 | Cues for one media file in one style (cues JSON v1). |
| `CueList.to_dict()` | 40 | Plain dict ready for JSON. |
| `CueList.save(path)` | 44 | Write as pretty UTF-8 JSON. |
| `make_cues(transcript, style, style_name)` | 74 | Chunk the transcript's words into cues that respect the style's limits. |
| `wrap_lines(text, line_length)` | 161 | Split text into two balanced lines when it is longer than `line_length`. |

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

### engine/legendaria_engine/review/glossary.py — 127 lines
Glossary files: names and terms the transcription must get right.

| Function / class | Line | What it does |
|---|---|---|
| `fold(text)` | 28 | Lowercase without accents or surrounding punctuation, for comparisons. |
| `split_entry(line)` | 35 | A parsed line: (wrong, right), a term, or None for blanks and comments. |
| `class Glossary` | 48 | Merged terms (in order, unique) and explicit fixes keyed by folded wrong text. |
| `Glossary.add_term(term)` | 55 | Add a term unless an equal one (ignoring case and accents) is there. |
| `Glossary.merge_text(text)` | 60 | Add every entry of a glossary file's text. |
| `global_file()` | 75 | The user's glossary for every project: `<config dir>/glossary.txt`. |
| `project_file(media)` | 80 | The glossary next to a media file: `legendaria-glossary.txt`. |
| `load(extra, media, use_global)` | 85 | Global glossary, then the project one next to `media`, then `extra` files. |
| `add_entry(path, entry)` | 105 | Append a term or a 'wrong -> right' line; returns False if it was already there. |

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
- `blender_addon/tests/`: `test_i18n.py` (every UI string translated, no unused or mismatched entries), `test_installer.py` (uv asset names, checksum, extraction, versions), `test_source_rules.py` (Blender API pitfalls, e.g. confirm-dialog icons), `test_timecode.py`, `test_engine_bridge.py` (fake flosub), `conftest.py` (imports the add-on package without bpy), `blender_smoke.py` (headless, inside Blender; `--real` runs flosub), `ui_walkthrough.py` (GUI session with screenshots under xvfb; `--install confirm|run` tests the Install engine flow).

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

### blender_addon/legendaria/engine_bridge.py — 189 lines
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
| `class EngineJob` | 113 | A running `flosub --progress json ...` process whose events can be polled. |
| `EngineJob.poll()` | 141 | Events received since the last call (never blocks). |
| `EngineJob.finished()` | 151 | True once the process has exited and all of its output has been read. |
| `EngineJob.returncode()` | 156 | Exit code, or None while running. |
| `EngineJob.stderr_tail()` | 160 | Last lines the engine wrote to stderr (for error reports). |
| `EngineJob.cancel()` | 164 | Stop the engine: terminate, then kill if it does not exit quickly. |
| `EngineJob.wait(timeout)` | 185 | Block until the process exits and its output is read (tests and scripts, not the UI). |

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

### blender_addon/legendaria/operators.py — 644 lines
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
| `LEGENDARIA_OT_generate.handle_event(event)` | 240 | Update progress and status from one engine event. |
| `LEGENDARIA_OT_generate.modal(context, event)` | 278 | Poll the engine on each timer tick; Esc or the Cancel button stops it. |
| `LEGENDARIA_OT_generate.cleanup(context)` | 319 | Remove the timer and mark the job as stopped. |
| `class LEGENDARIA_OT_cancel` | 329 | Stop the running transcription |
| `LEGENDARIA_OT_cancel.execute(context)` | 335 | Ask the running generate operator to stop. |
| `class LEGENDARIA_OT_reapply_style` | 341 | Rebuild the captions from the saved transcript with the chosen style, without transcribing again |
| `LEGENDARIA_OT_reapply_style.poll(context)` | 349 | Needs a saved transcript and no running job. |
| `LEGENDARIA_OT_reapply_style.invoke(context, event)` | 354 | Ask before replacing captions. |
| `LEGENDARIA_OT_reapply_style.execute(context)` | 372 | Run `flosub export --style` on the saved transcript and rebuild the strips. |
| `class LEGENDARIA_OT_export` | 415 | Save the captions on the channel as an SRT or VTT file (with your edits) |
| `LEGENDARIA_OT_export.export_channel(context)` | 431 | Channel to export: the one used last, else the setting, else the active strip's. |
| `LEGENDARIA_OT_export.invoke(context, event)` | 437 | Open the file browser with a sensible default name. |
| `LEGENDARIA_OT_export.execute(context)` | 448 | Write the file from the text strips. |
| `class LEGENDARIA_OT_exact_colors` | 472 | Use the Standard view transform so captions keep their real colors |
| `LEGENDARIA_OT_exact_colors.execute(context)` | 479 | Switch the scene's view transform to Standard. |
| `class LEGENDARIA_OT_refresh_engine` | 486 | Look for the transcription engine again and reload its models |
| `LEGENDARIA_OT_refresh_engine.execute(context)` | 492 | Re-run engine detection. |
| `install_status()` | 501 | Translated status line and progress of the running install (for panel and preferences). |
| `class LEGENDARIA_OT_install_engine` | 511 | Download and set up the transcription engine (uv, Python, flosub and the default model) |
| `LEGENDARIA_OT_install_engine.poll(context)` | 520 | Not while an install is already running. |
| `LEGENDARIA_OT_install_engine.invoke(context, event)` | 524 | Explain what will be downloaded and ask first. |
| `LEGENDARIA_OT_install_engine.execute(context)` | 544 | Start the installer thread and poll it from a timer. |
| `LEGENDARIA_OT_install_engine.modal(context, event)` | 554 | Redraw while installing; report the result at the end. |
| `class LEGENDARIA_OT_cancel_install` | 577 | Stop installing the engine |
| `LEGENDARIA_OT_cancel_install.execute(context)` | 583 | Ask the installer to stop. |
| `class LEGENDARIA_OT_uninstall_engine` | 590 | Delete the engine installed by this add-on (downloaded models are kept) |
| `LEGENDARIA_OT_uninstall_engine.poll(context)` | 597 | Only when the add-on's own engine is installed and idle. |
| `LEGENDARIA_OT_uninstall_engine.invoke(context, event)` | 601 | Ask first. |
| `LEGENDARIA_OT_uninstall_engine.execute(context)` | 614 | Remove the engine folder and look for another engine. |
| `register()` | 635 | Register the operators. |
| `unregister()` | 641 | Remove the operators. |

### blender_addon/legendaria/panel.py — 127 lines
Sidebar panel in the Video Sequencer ("Legendária" tab).

| Function / class | Line | What it does |
|---|---|---|
| `draw_engine_box(layout)` | 12 | Engine install / update / progress UI. Returns True when the engine is ready to use. |
| `class LEGENDARIA_PT_main` | 44 | Generate, re-style and export captions |
| `LEGENDARIA_PT_main.draw(context)` | 53 | Engine status, source, options, generate/progress, re-style and export. |
| `register()` | 118 | Register the panel. |
| `unregister()` | 124 | Remove the panel. |

### blender_addon/legendaria/preferences.py — 51 lines
Add-on preferences: where the engine is, and its detected status.

| Function / class | Line | What it does |
|---|---|---|
| `class LegendariaPreferences` | 11 | Shown under Edit → Preferences → Add-ons → Legendária. |
| `LegendariaPreferences.draw(context)` | 23 | Engine path, detection result and a refresh button. |
| `register()` | 42 | Register the preferences class. |
| `unregister()` | 48 | Remove the preferences class. |

### blender_addon/legendaria/properties.py — 145 lines
Scene settings and the engine info cache (models, languages, styles from `flosub`).

| Function / class | Line | What it does |
|---|---|---|
| `addon_prefs(context)` | 36 | The add-on preferences, or None when the add-on is not enabled through Preferences. |
| `refresh_engine_info(context)` | 43 | Locate flosub and reload models, languages and styles. Returns True when found. |
| `class LegendariaSettings` | 99 | Per-scene options and the state of the running job. |
| `register()` | 134 | Register the settings and attach them to scenes. |
| `unregister()` | 141 | Remove the settings. |

### blender_addon/legendaria/strips.py — 194 lines
Cues ↔ text strips: create caption strips, find the ones we made, read them back.

| Function / class | Line | What it does |
|---|---|---|
| `scene_fps(scene)` | 17 | Real frames per second (fps / fps_base). |
| `load_preset(style)` | 22 | Strip style for a cue style: user override in the config dir, else the shipped preset. |
| `apply_preset(strip, preset, resolution_y)` | 31 | Apply a style preset to a text strip; font sizes are scaled from 1080 px. |
| `is_ours(strip)` | 56 | True for strips created by the add-on. |
| `overlaps(strip, frame_start, frame_end)` | 61 | Whether the strip's visible range intersects [frame_start, frame_end). |
| `tagged_in_range(editor, channel, frame_start, frame_end, by_midpoint)` | 66 | Our caption strips on `channel` in the range (they would be replaced). |
| `foreign_in_range(editor, channel, frame_start, frame_end)` | 85 | Strips not made by us on `channel` in the range (we never touch these). |
| `pick_channel(editor, media_strip, frame_start, frame_end)` | 94 | First channel above the media strip that holds only our captions (or nothing) in range. |
| `media_range(media_strip)` | 102 | (content_start, visible_start, visible_end) frames of a MOVIE/SOUND strip. |
| `load_cues(path)` | 110 | Read a cues JSON (v1) written by `flosub ... --format cues`. |
| `create_strips(scene, editor, cues, media_strip, channel, style, frame_range)` | 118 | Replace our strips on `channel` with new cue strips; returns the new strips. |
| `selected_caption_range(editor)` | 166 | Frame span of the selected caption strips, or None when none is selected. |
| `read_cues(scene, editor, channel, only_ours)` | 174 | Text strips on `channel` as (start_s, end_s, text) from frame 0, sorted by time. |

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

- Plan 02 (Blender add-on): done (steps 09–12).
- **Plan 03, accuracy:** stage 3a (glossary, hotwords, deterministic fixes, suggestions) done (step 18). Next: 3b (LLM reviewer), 3c (Blender UI).
- Then plan 04 (CapCut animations — MVP look "one-word pop" decided, §8; style catalog §9 — `.ass` export / exact preview / burn-in / SRT alignment — §6), plan 05 (local API + `flosub gui` web interface).
- Plan 06 (Blender UX, draft): the owner finds the VSE hard to reach; one-click setup and entry points.
- **Known issues:** `dev-docs/known-issues.md` (KI-001, high: desktop freeze when loading `medium` from Blender).
- Backlog: plan 01, section 8.
