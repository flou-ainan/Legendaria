# Step 12 — Stage 2c: regenerate a time range (engine 0.1.0.dev2)

**Date:** 2026-10-24 (overnight, autonomous)
**Agent/author:** Claude Code (Opus 5.5)
**Related plan:** planning/plan_02_blender_addon.md (R4, §6 2c)

## What was done

- **Engine (0.1.0.dev2):**
  - `transcribe --clip START,END` passes faster-whisper's `clip_timestamps`. It was checked first that output times stay **absolute** and that the clip is honoured with `vad_filter=True`. Progress covers the clip length.
  - `--update saved.json` merges the range into the saved transcript through `Transcript.merged_with()`, **word by word**: old segments keep only their words outside the range, new segments only their words inside, so nothing is duplicated or lost at the boundaries.
  - `parse_clip` validates the input; `--update` requires `--clip`.
- **Add-on:**
  - `generate` has a `range_only` mode, shown in the panel as **"Regenerate range"** next to "Re-apply style".
  - The range is the scene's **preview range** or, when there is none, the span of the **selected captions**. It is intersected with the video, and the video used is the one from the last run.
  - Confirmation: "{count} captions between {start} and {end} will be replaced…".
  - The engine is called with `--clip` and `--update <saved transcript>`.
  - `strips.create_strips(frame_range=...)` replaces only captions whose middle frame is inside the range, and trims new strips so they never overlap the captions that stay or each other.
  - `MIN_ENGINE` and the installer spec are now `0.1.0.dev2`.
- **Tests:**
  - Engine: merge by range, a boundary-crossing segment split word by word, clip parsing, `--update` without `--clip` (55 total).
  - `blender_smoke.py`:
    - every `icon=` used in the UI exists in that Blender (an invalid one would break the panel draw);
    - **real range regeneration**, with the plan counting the captions in range, the engine run, captions outside the range untouched, and no overlaps.

## Bug found and fixed

The first version merged by segment midpoint. A segment that starts inside the range but has its middle outside was kept whole, so its first words duplicated the regenerated ones and two caption strips overlapped. The smoke test's "no overlapping captions" check caught it. Merging is now word-level, and the add-on also prevents overlaps among the new strips.

## How it was tested

- Engine pytest: 55 passed. Add-on pytest: 35 passed. Ruff is clean.
- Real CLI run: full transcript with `small`, then `--clip 10,20 --update` with `tiny`. The 8 segments outside are identical, the 2 inside were replaced, and progress went 0→10 s.
- Inside Blender: `blender_smoke.py --real` 28/28 on 4.2.23 and 5.2.3; the CI mode (no engine output) 20/20.
- GUI (xvfb, 5.2.3, pt_BR): the panel shows "Reaplicar estilo | Regerar trecho".

## Pending / next steps

- Release engine 0.1.0.dev2 (tag after merge).
- The owner tries it on real videos.
- Plan 03: CapCut-style animations and style presets; needs the owner's input on the look.
