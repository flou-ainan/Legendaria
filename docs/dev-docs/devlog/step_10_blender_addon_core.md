# Step 10 — Stage 2a: Blender add-on core

**Date:** 2026-10-24 (overnight, autonomous, at the owner's request)
**Agent/author:** Claude Code (Opus 5.5)
**Related plan:** planning/plan_02_blender_addon.md (§4, stage 2a)

## What was done

- **`blender_addon/legendaria/`**, a Blender 4.2+ extension (GPL-3.0-or-later, manifest with permissions):
  - `engine_bridge`: finds `flosub` in this order: custom path, managed install (2b), PATH, then per-OS user dirs. Runs it without a shell (no console window on Windows), reads JSON events on a thread into a queue, supports cancel, and only reports `finished` once all output is read.
  - `compat`: feature-detected API differences, verified on 4.2.23 and 5.2.3: `sequences`→`strips`, `frame_end`→`length` in `new_effect`, `align_x/y`→`alignment_x` + `anchor_x/y`.
  - `strips`:
    - Cue → text strip mapping: `media.frame_start + round(s × fps)`, clipped to the visible (trimmed) range.
    - Strips are tagged (`legendaria_cue`) and their word timings are kept for the future animation plan.
    - Replacement only touches tagged strips; channel auto-pick skips channels holding foreign strips.
    - Presets are scaled from 1080 px, and the user can override them in the config dir.
    - Strips are read back for export.
  - `operators`:
    - `generate`: a modal timer, so the UI never freezes; Esc or Cancel stops it; invoke_confirm before replacing (R3).
    - `cancel`, `reapply_style` (uses the media of the last run, `flosub export --style`), `export` (SRT/VTT with a file browser), `refresh_engine`.
  - `properties`: per-scene settings. Model, language and style menus are filled from `flosub models list --json` and `config show`; models not yet downloaded show "↓" and download automatically (R2).
  - `panel`, `preferences`, `i18n` (`locales/pt_BR.json`, registered in the default and Operator contexts).
- **Tests:**
  - `test_i18n.py` scans the source (labels, buttons, tooltips, reports, enum items) and fails on untranslated strings or mismatched placeholders.
  - `test_timecode.py`, and `test_engine_bridge.py` with a fake `flosub` covering events, noise, failure codes and cancel.
  - `blender_smoke.py` (23 checks) and `ui_walkthrough.py` (scripted GUI with screenshots).
- **CI:** add-on pure-Python tests on all 3 OSes, plus a `blender` job that downloads Blender 4.2.23 and 5.2.3 (SHA-256 checked, cached), installs the engine with `uv tool`, runs the smoke test and builds the extension zip.
- **Tooling:** `tools/project_map.py` now skips private helpers; `ruff.toml` ignores RUF012 in the add-on (Blender's `bl_options = {...}` idiom).
- **Dev machine:** `flosub` installed globally as an editable `uv tool` (`uv tool install --editable "./engine[cuda]"`), so Blender finds it on PATH.

## Problems found and fixed

1. **Blender 4.2 places a new sound strip one frame after the requested frame** (11 instead of 10). The add-on was right (it maps from the strip's real `frame_start`); the test's assumption was wrong. Fixed the test.
2. **Xvfb screenshots came out black:** Blender's own screenshot reads an empty GL buffer. The walkthrough now grabs the X screen with ImageMagick `import` when `LEGENDARIA_X_CAPTURE` is set.
3. **Walkthrough crash (segfault)** from calling `sequencer.view_all` without a region override, in the test script only. The call was removed.
4. **The panel tab cannot be selected from Python** in 4.2 (`active_panel_category` is "UNSUPPORTED"). For screenshots only, the walkthrough registers copies of the panel in the Strip and Tool tabs.
5. **UI wording seen in screenshots:**
   - Blender's own pt_BR dictionary translated our "Language" label as "Linguagem"; the property is now named "Spoken language" ("Idioma falado").
   - Channel 0 now shows "Auto".
6. **Re-apply style** used the active strip; it now uses the media strip of the last run.

## How it was tested

- `uvx pytest blender_addon/tests`: 16 passed. `uv run pytest` (engine): 51 passed. Ruff check and format are clean.
- **Inside Blender, headless, on 4.2.23 LTS and 5.2.3 LTS:** `blender_smoke.py --real` passes 23/23 on both. It covers:
  - fixture cues → strips, frame mapping, presets;
  - replacement detection and no duplicates;
  - hand-made strips untouched and foreign strips blocking a manual channel;
  - export time base and the SRT operator;
  - pt_BR translation, engine detection, model list;
  - a **real `flosub` transcription inside Blender** (31 captions ≤ 22 chars);
  - **re-apply style** to subtitles (12 cues).
- **Extension packaging:** `extension validate` and `build` succeed. `install-file` into an isolated `BLENDER_USER_RESOURCES` on both versions: enabled as `bl_ext.user_default.legendaria`; preferences, operators and panel registered; engine found; defaults `captions` / `small`.
- **Scripted GUI sessions** (xvfb, real installed extension, en_US and pt_BR, both versions) check: idle panel → Generate (progress bar "Transcrevendo… 75%", Cancel shown, fields locked) → 31 caption strips with the status message → Generate again → the confirmation dialog "Substituir legendas? 31 legendas no canal 2 serão substituídas…".
- Not yet verified by a human: real use with the mouse, hand-editing then exporting, a first-time model download from the UI, Windows and macOS.

## Pending / next steps

- The owner tries it on real videos (instructions in the morning summary).
- Stage 2b: the "Install engine" button. Stage 2c: regenerate a time range.
- Good screenshots with a real video for the README and the future docs site. The current ones show scratch paths.
