# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Engine versions are the PyPI package `legendaria` (CLI `flosub`); the Blender add-on has its own version in its manifest.

## [Unreleased]

### Changed
- **Direction:** a local web editor (`flosub serve`, plan 07) becomes the main interface; the Blender add-on is frozen (bug fixes only, ADR-014).

### Added
- **Blender add-on** (extension `legendaria` 0.1.0, Blender 4.2+, not yet released): "Legendária" tab in the Video Sequencer; pick model (auto-download), language and style; generate CapCut-style caption strips in the background with progress and cancel; confirmation before replacing captions; re-apply a style without transcribing again; export SRT/VTT from the edited strips; English and Brazilian Portuguese UI; style presets in JSON.
- Add-on **"Install engine"** button: downloads uv, Python 3.11, the engine (with GPU support when an NVIDIA card is present) and the default model into one folder, with progress and cancel; uninstall and "engine too old" warning with update.
- Add-on: caption colors are exact. Generating switches the scene to the Standard view transform (Blender's default AgX/Filmic turned yellow into a pale white), and the panel offers "Fix caption colors".
- Add-on: "One word (pop)" style (yellow, bold) is the default.
- Add-on **Export ASS** (styled subtitles with the caption look, from the edited strips) and **Exact preview**: the captions rendered by libass as a transparent movie above the strips (the caption channel is muted), so the scene's normal render gives the final burned-in video; "Remove exact preview" brings the strips back. Needs FFmpeg.
- Add-on: preset font sizes scale with the render's shorter side, so vertical videos keep the proportions.
- Add-on **glossary and review** (needs engine 0.1.0.dev4): pick the active glossary in a drop-down, create, import, export or edit glossaries; "Use glossary" toggle; "Add to glossary" from a selected caption or a suggestion (to the active glossary or the video's folder); "Review captions" lists suggested corrections with checkboxes; "Apply corrections" updates the transcript and rebuilds only the affected captions. "Use AI (experimental)" also asks the LLM reviewer.
- Add-on **"Regenerate range"**: redo only the preview range or the selected captions, with confirmation; captions outside are untouched.
- Project documentation, brand kit, contribution setup (CONTRIBUTING, Code of Conduct, security policy, templates, ruff, pre-commit, CI on Linux / macOS / Windows and inside Blender 4.2 / 5.2), `tools/project_map.py`.

## [engine 0.1.0.dev4] - 2026-10-26

### Added
- **Styled subtitles (`.ass`)**: `--format ass` on `transcribe` and `export` with the look of each style from the config (`styles.<name>.ass`: font, colors, outline, box, position, uppercase, `pop` animation). The default `pop` style is yellow, one word at a time, with the pop 70 → 112 → 100 % over 170 ms. `export` also accepts an edited cues JSON.
- **`flosub burn VIDEO`**: a copy of the video with the subtitles drawn in (FFmpeg + libass; encoder arguments in config `burn`). **`flosub overlay`**: the subtitles alone on a transparent QuickTime Animation `.mov`, for editors. FFmpeg comes from config `ffmpeg` or PATH.
- **Glossary** (plain text: terms and `wrong -> right` fixes) with a **library of named glossaries** and an active one (`flosub glossary list|new|use|import|export|delete|show|path|add`), a project glossary next to the media, and `--glossary FILE|NAME`.
- Glossary terms steer Whisper while transcribing (`hotwords`); `--no-glossary` turns it off.
- **LLM reviewer (experimental, off by default):** `flosub review --llm` uses any OpenAI-compatible server (Ollama, LM Studio, llama.cpp; OpenAI, Gemini, Anthropic or OpenRouter with your key). The model only proposes changed lines; a guard rejects rewrites, deletions, translations and invented words. `flosub llm check|providers`; editable prompt; falls back to the glossary when no server answers.
- **Review without AI:** `flosub review FILE.json` (or `transcribe --review`) suggests explicit fixes and close matches of uncertain words, written to `<name>.review.json` (or applied directly in `auto` mode); `flosub review apply` applies the chosen suggestions and re-times the words.

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
