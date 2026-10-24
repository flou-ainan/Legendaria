# Project Map — Legendária

> A condensed map of the project, so agents and people can find what they need without rereading the code.
> **Update this file with every change to the project** (files, functions, stack, structure). Conventions: `docs/dev-docs/README.md`.

**Last updated:** 2026-10-24 — step 05 (brand kit / logo). No code yet.

---

## 1. Overview

**Legendária** ("free subtitles, CapCut style") is a free, open-source automatic subtitle creator, inspired by CapCut's auto captions. Names (ADR-009): product **Legendária**; repository, Python package and add-on id `legendaria`; CLI command `flosub`.

What it does:

- Transcribes the audio locally on the GPU, with per-word timings.
- Turns the result into **editable text strips in Blender's Video Sequence Editor**.
- Exports SRT/VTT, or renders the video with the subtitles burned in.

Goals: a "next → next → finish" install for end users; a hackable setup driven by JSON configs; friendly to contributors; Linux, macOS and Windows 10+; UI and user docs in English and pt-BR (open to more languages).

**Current state:** planning. The MVP and the roadmap are in `dev-docs/planning/plan_01_mvp_engine_blender.md`.

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
| GPU acceleration | CUDA 12 via `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` 9 (pip), no PyTorch; Linux and Windows |
| Media decoding | PyAV (bundled with faster-whisper) / FFmpeg |
| Editor | Blender 4.2+ Video Sequence Editor (`bpy`), extension format |
| Language | Python 3.10+ (engine) / Blender's bundled Python (add-on) |
| Config | JSON + JSON Schema, `platformdirs` for per-OS paths |
| i18n | `bpy.app.translations` + `locales/<lang>.json` (en source, pt_BR maintained) |
| Tests | pytest |
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
├── AGENTS.md                # instructions for any AI agent
├── CLAUDE.md                # points to AGENTS.md
├── README.md                # user-facing, English
├── README.pt-BR.md          # user-facing, Brazilian Portuguese
├── LICENSE                  # MIT
├── .gitignore
├── assets/
│   └── brand/           # logo kit: SVG symbol/icons/lockups, PNGs, favicon (see its README)
└── docs/
    ├── PROJECT.md           # this file
    └── dev-docs/
        ├── README.md        # documentation conventions
        ├── planning/        # plans (before implementing)
        ├── devlog/          # executed steps
        ├── decisions/       # ADRs
        └── references/      # origin_brainstorm.md
```

The target layout for `engine/` and `blender_addon/` is in plan 01, section 4.3. It moves here once those folders exist.

## 6. File map

### assets/brand/source/generate_brand_svgs.py — 60 lines
Dev tool that writes the brand SVGs into `assets/brand/`. Constants: `GRAD` (the symbol gradient), `PATHS` (symbol strokes), `SYMBOL_VB`, `SMALL` / `SMALL_GRAD` (small icon). The lockup text has to be converted to paths with Inkscape afterwards (see `assets/brand/README.md`).

| Function / class | Line | What it does |
|---|---|---|
| `group(stroke, width=37)` | 21 | Wraps the symbol strokes in a `<g>` with the given stroke paint and width |
| `write(name, body, vb, w, h, title)` | 24 | Writes one SVG file with a viewBox, title and accessible label |
| `lockup(name, font, weight, fill, bg)` | 51 | Writes a symbol + "Legendária" wordmark SVG (text, not yet paths) |

There is no engine or add-on code yet. Each source file will get an entry like this:

```markdown
### path/file.py — N lines
Short description of the file's role.

| Function / class | Line | What it does |
|---|---|---|
| `function_name(args)` | 12 | ... |
```

## 7. In progress

- Plan 01 approved, with no open questions left. `main` is protected: every change goes through a PR (ADR-008).
- Brand kit in `assets/brand/`; wordmark font pending (Montserrat or Nunito).
- Next: the rest of stage 0 (project foundation), then stage 1 (engine).
