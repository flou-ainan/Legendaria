# Plan 02 — Blender add-on (MVP stage 2) and caption-style cues

**Status:** approved (owner, 2026-10-24). Stages 2a (steps 09–10) and 2b (step 11) done; 2c next
**Date:** 2026-10-24
**Builds on:** plan 01 (section 4.5), ADR-002, ADR-003, ADR-005, ADR-006

## 1. Goal

Inside Blender 4.2+ the user selects a video strip, picks a model, clicks **Generate subtitles**, and gets **short, CapCut-style captions** as editable text strips. The UI never freezes, models download automatically, and the user's edits are never overwritten silently.

## 2. Requirements from the owner (2026-10-24)

| # | Requirement | Where |
|---|---|---|
| R1 | Film-style subtitles are right for SRT/VTT, but **in Blender the default is CapCut style**: short phrases that stay on screen briefly (animation comes in a later plan) | §3 cues, §4 add-on |
| R2 | **Choose the model inside Blender**, with **automatic download** | §4.3 |
| R3 | **Warn before overwriting** existing captions when generating again | §4.4 |
| R4 | **Regenerate only a part** of the video. Feasible: faster-whisper's `clip_timestamps` transcribes a time range | stage 2c (§6) |

## 3. Engine: cues (caption chunking)

The transcript JSON (v1, with word timings) stays the source of truth. A new step turns it into **cues**, the timed text blocks shown on screen, following a **style** defined in JSON:

- **`captions`** (Blender default): at most 4 words / 22 characters, 0.3–2.2 s per cue, a break at punctuation and at pauses > 0.5 s.
- **`subtitles`** (SRT/VTT default): at most 84 characters (2 lines of 42), 1–6 s per cue, a break at sentence punctuation and at pauses > 1 s.

The styles live in `config.json` under `"styles"`, so users can tune them or add their own (ADR-006).

Changes:

- **[NEW] `legendaria_engine/cues.py`:**
  - `Cue` (start, end, text, words).
  - `make_cues(transcript, style_rules)`: greedy chunking over the words, honoring the max words/chars/duration and the break rules.
  - `min_duration` handling: extends a cue up to the next cue's start.
  - Falls back to segment text when a segment has no word timings.
- **[CHANGE] `formats.py`:** SRT/VTT are written from cues, not from raw segments.
- **[NEW] Cues JSON v1** (`<stem>.cues.json`): `{version, style, source, language, cues: [...]}` plus `schemas/cues.schema.json`.
- **[CHANGE] CLI:**
  - `transcribe` and `export` accept `--style captions|subtitles|<custom>`. The default comes from config: `subtitles` for files.
  - Format `cues` (cues JSON) joins json/srt/vtt.
  - `flosub transcribe video.mp4 --style captions --format json,cues` is the add-on's call.
- **Tests:** chunking limits, punctuation and pause breaks, min-duration extension, a segment without words, custom styles from user config.

## 4. Blender add-on (`blender_addon/legendaria/`, GPL-3.0-or-later)

### 4.1 Compatibility

Blender **4.2 LTS to 5.x**. Real testing on **4.2.23** and **5.2.3** (portable copies in `~/Programs/`). `compat.py` hides the API differences: `sequences` vs `strips`, effect-creation arguments, text-strip property names, and the frame range attribute names, all verified on both versions.

### 4.2 Engine bridge

`engine_bridge.py` finds `flosub`, in this order:
1. The path set in the add-on preferences.
2. The managed install (stage 2b).
3. `flosub` on PATH, including `~/.local/bin`, `%APPDATA%\Python\Scripts` and other per-user locations that Blender may not have on its PATH.

It runs the engine with `subprocess.Popen` (argument list, no shell; on Windows, no console window), reads the JSON-lines events on a background thread into a queue, and kills the process on cancel. When no engine is found, the panel shows how to install it.

### 4.3 Panel ("Legendária" tab in the sequencer sidebar)

- **Source:** the active MOVIE/SOUND strip, shown by name, with a hint when none is selected.
- **Model:** a dropdown filled from `flosub models list --json`, marking installed models (✓), sizes, and the default. A model that is not installed is **downloaded automatically** when you generate, with progress in the UI ("Downloading model… 42%"). R2.
- **Language:** auto / pt / en (from the config's `ui_languages`).
- **Style:** captions (default) / subtitles.
- **Channel** for the captions.
- **Generate subtitles** button; while running, a progress bar, a status line and **Cancel**.
- **Export SRT / VTT:** from the text strips (after the user's edits).
- **Re-apply style:** rebuilds the strips from the saved transcript with a different style, without transcribing again (same overwrite warning as R3).

### 4.4 Generating and overwriting (R3)

- Strips created by the add-on are tagged (custom property `legendaria_cue`) and named `LGD 0001`, …
- Before generating, the operator counts the tagged strips on the target channel inside the source strip's time range. If there are any, a **confirmation dialog** says: "N captions on channel C will be replaced. Your edits to them will be lost." The user can cancel.
- Only tagged strips in that range are removed. Hand-made text strips are never touched.
- The transcript and cues JSON are saved next to the `.blend` in `//legendaria/` (or in a temp folder for unsaved files). Their path is stored on the scene, so "Re-apply style" and the future range regeneration can reuse them.

### 4.5 Strip creation

- One text strip per cue: `frame = media_strip_start + round(seconds × fps / fps_base)`, accounting for the media strip's trimmed head.
- Styling comes from `presets/captions.json` / `presets/subtitles.json` (font size, position, alignment, shadow, outline, box, wrap width), mapped through `compat.py`.
- The strip's text is the cue text; the word timings go in a custom property, for the later animation plan.

### 4.6 Export

Reads the text strips of the channel (tagged ones, or all text strips when none are tagged), sorted by `frame_final_start`, converts frames to seconds and writes SRT/VTT next to the `.blend`, or to a path picked in the file browser. Timestamp formatting is copied from the engine (ADR-003 consequence).

### 4.7 i18n (ADR-005)

All UI strings are in English in the code and registered through `bpy.app.translations` from `locales/<lang>.json`; `pt_BR.json` is complete. `locales/README.md` explains how to add a language.

### 4.8 Files

```
blender_addon/legendaria/
├── blender_manifest.toml   # id "legendaria", Blender >= 4.2, GPL-3.0-or-later
├── LICENSE
├── __init__.py             # register / unregister
├── compat.py               # VSE API differences 4.2 … 5.x
├── engine_bridge.py        # find flosub, run it, parse events (thread + queue)
├── i18n.py                 # load locales/*.json into bpy.app.translations
├── preferences.py          # engine path, detected status
├── properties.py           # scene settings: model, language, style, channel, job state
├── operators.py            # generate (modal), cancel, re-apply style, export, refresh models
├── strips.py               # cues → strips; strips → cues; overwrite detection
├── timecode.py             # frames ↔ seconds, SRT/VTT timestamps (pure Python, testable)
├── panel.py                # sidebar UI
├── presets/captions.json, presets/subtitles.json
└── locales/pt_BR.json, locales/README.md
```

Packaged as a zip for "Install from Disk".

## 5. Testing

- Engine: pytest for cues and formats (CI on 3 OSes).
- Add-on, headless: a `blender -b --python` test script runs on **4.2.23 and 5.2.3**. It registers the add-on, creates strips from a fixture cues JSON, checks the overwrite detection, exports SRT and compares it to the expected text, and checks that the pt_BR translations load.
- Real end-to-end run: drive the operator logic headlessly against the real `flosub` on a public-domain clip.
- Manual UI check by the owner: the panel, the progress bar, the confirmation dialog, cancel, the Portuguese UI.
- Blender in CI is deferred to the backlog: the downloads are heavy, and caching is needed.

## 6. Stages

- **2a (this plan, now):** engine cues + add-on core (§3, §4).
- **2b (done, step 11):** "Install engine" button (uv bootstrap, `cuda` extra when an NVIDIA GPU is detected). See plan 01 decision 9. As built:
  - uv **0.13.0** pinned (SHA-256 checked) for Linux/macOS/Windows on x86_64/arm64.
  - Python 3.11 and the uv cache are kept inside `<data dir>/legendaria/engine/`; the cache is deleted after install, since the venv is self-contained.
  - Installs `legendaria>=0.1.0.dev1,<0.2` (pre-releases allowed), then downloads `small`.
  - Confirmation dialog shows the download size: ~1.3 GB, or ~3.5 GB with GPU.
  - Progress ("Step n of 4") with Cancel; Uninstall in preferences.
  - The add-on warns when the engine is older than `MIN_ENGINE` and offers "Update engine".
  - `LEGENDARIA_INSTALL_CUDA=0|1` overrides GPU detection.
- **2c:** regenerate a time range (R4):
  - Engine `--clip START,END` (faster-whisper `clip_timestamps`).
  - The add-on uses the scene's preview range (or the selected caption strips' span), replaces only the tagged strips in that range, and asks for confirmation as in R3.
- **Later (plan 03, "CapCut styles"):** animations (pop-in, current-word highlight, karaoke colors), style presets gallery, emphasis words.

## 7. Definition of done (2a)

- [x] `flosub transcribe clip.mp3 --style captions --format json,cues` gives short cues within the limits; subtitles style unchanged for SRT/VTT (step 09).
- [x] Headless Blender tests pass on 4.2.23 and 5.2.3 (23/23, including a real `flosub` run).
- [x] In Blender: select a video → Generate → progress with no frozen UI → caption strips on the chosen channel, aligned with the speech (scripted GUI session under xvfb, both versions). Download progress with a not-yet-installed model: covered by the engine events; the GUI run used an installed model. **Owner to check on real videos.**
- [x] Generating again warns before replacing (dialog captured in en and pt_BR); hand-made strips survive (smoke test). Cancel in the dialog: Blender built-in.
- [x] Export SRT reads the strips (smoke test); editing a strip by hand: **owner to check in the UI**.
- [x] UI in Portuguese when Blender's language is Portuguese (Brazil) (screenshots; i18n coverage test).
- [x] Docs: `PROJECT.md`, devlog, CHANGELOG.
