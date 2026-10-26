# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Engine versions are the PyPI package `legendaria` (CLI `flosub`); the Blender add-on has its own version in its manifest.

## [Unreleased]

### Added
- **Blender add-on** (extension `legendaria` 0.1.0, Blender 4.2+, not yet released): "Legendária" tab in the Video Sequencer; pick model (auto-download), language and style; generate CapCut-style caption strips in the background with progress and cancel; confirmation before replacing captions; re-apply a style without transcribing again; export SRT/VTT from the edited strips; English and Brazilian Portuguese UI; style presets in JSON.
- Add-on **"Install engine"** button: downloads uv, Python 3.11, the engine (with GPU support when an NVIDIA card is present) and the default model into one folder, with progress and cancel; uninstall and "engine too old" warning with update.
- Add-on: "One word (pop)" style (yellow, bold) is the default.
- Add-on **"Regenerate range"**: redo only the preview range or the selected captions, with confirmation; captions outside are untouched.
- Project documentation, brand kit, contribution setup (CONTRIBUTING, Code of Conduct, security policy, templates, ruff, pre-commit, CI on Linux / macOS / Windows and inside Blender 4.2 / 5.2), `tools/project_map.py`.

## [engine 0.1.0.dev3] - 2026-10-26

### Added
- Style `pop`: one word at a time (two when the first has at most 3 letters), glued word pieces ("bem" + "-vindas") never split, short silences filled. New style keys `join_short` and `fill_gaps`; `max_words` now counts readable words.

## [engine 0.1.0.dev2] - 2026-10-24

### Added
- `--clip START,END` transcribes only a time range (times stay absolute); `--update saved.json` merges that range into a saved transcript word by word.

## [engine 0.1.0.dev1] - 2026-10-24

### Added
- Cue styles: `captions` (short CapCut-style phrases) and `subtitles` (film-style lines, wrapped in two lines), configurable in JSON; `--style` on `transcribe` and `export`; new `cues` output format (`<name>.cues.json`). Needed by the Blender add-on.

### Fixed
- Output names keep dots in the media name (`a.b.mp4` → `a.b.srt`).
- Words attached to the previous one (Portuguese "-se", English "'s") are no longer split by a space.

## [engine 0.1.0.dev0] - 2026-10-24

### Added
- First pre-release of the transcription engine `flosub`: local faster-whisper transcription on NVIDIA GPU (fp16) or CPU (int8) with automatic GPU→CPU fallback; per-word timings; JSON (v1), SRT and VTT output; `export`, `models list|download` and `config show|path` commands; layered JSON config and model catalog with JSON Schemas; JSON-lines progress events.
