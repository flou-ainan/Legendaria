# Step 09 — Plan 02 and engine cues (captions / subtitles styles)

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_02_blender_addon.md (§3)

## What was done

- **Plan 02 written:** the Blender add-on, with the owner's requirements:
  - R1: CapCut-style captions by default in Blender.
  - R2: model choice in Blender, with automatic download.
  - R3: warn before overwriting.
  - R4: regenerate only a time range. It is feasible through faster-whisper's `clip_timestamps`, and is scheduled as stage 2c rather than left as tech debt.
- **Engine cues** (`legendaria_engine/cues.py`):
  - `make_cues` groups words into on-screen cues by a style: max words / chars / duration, a break after punctuation, a break on pauses and on segments, and a minimum duration stretched without overlapping the next cue.
  - `wrap_lines` balances long subtitles into two lines.
  - Cues JSON v1 (`<name>.cues.json`) with a schema.
- **Styles in config:**
  - `subtitles` (the default for files): 84 chars, 2×42 lines, 1–6 s.
  - `captions` (CapCut-like): 4 words, 22 chars, 0.3–2.2 s, a break at `.,!?;:…` and at pauses > 0.5 s.
  - Users can tune them or add their own; they are validated with errors that name the bad key.
- **CLI:**
  - `--style` on `transcribe` and `export`.
  - Format `cues`.
  - `export` re-chunks a saved transcript in any style without transcribing again.
- **Writers:** SRT/VTT are now built from cues.
- **Environment correction:** Blender was **not** installed; `~/.local/bin/blender` was a dangling symlink to a removed 4.2.0 folder. Steps 01 and plan 01 said otherwise; both are now annotated. Portable **Blender 4.2.23 LTS** and **5.2.3** were downloaded into `~/Programs/`, with their official SHA-256 checked, for add-on testing.

## Bugs found and fixed

1. **Dotted media names:** `aula.parte1.mp4` would have produced `aula.srt`, because `with_suffix` replaced `.parte1`. Output paths are now built by appending.
2. **Real-clip test:** the captions showed "Bem -se -se o". Whisper marks new words with a leading space, and attached pieces (`-se`, `'s`) have none. Words are now joined as Whisper spells them.

## How it was tested

- `uv run pytest`: 51 passed (new: `test_cues.py`, style config tests, cues schema, CLI style and dotted-name tests).
- Real run on the 106 s Portuguese clip with `--style captions`: 98 cues, at most 4 words and 22 chars, durations 0.30 / 0.77 / 1.74 s (min / avg / max). Re-chunking from the saved JSON with `export --style captions` works.

## Pending / next steps

- Stage 2a, the add-on itself (next PR).
