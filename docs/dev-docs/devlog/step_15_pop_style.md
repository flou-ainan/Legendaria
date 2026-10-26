# Step 15 — One-word "pop" style (the MVP look) and new test samples

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plans:** plan 04 (§8, §9), plan 06 (draft)

## What was done

- **Owner feedback** on the first `.ass` sample: the blocks were too big, the zoom hit the whole line, the karaoke fill was unwanted. For the MVP: one word at a time (two when it makes sense or for compound words), only that word popped and highlighted.
- **Engine (0.1.0.dev3):**
  - `cues.py` counts **readable words**: pieces with no leading space ("-vindas", "'s") are glued to their word and never start a cue.
  - New style keys `join_short` (a word with ≤ N letters takes the next one) and `fill_gaps` (extend a cue to the next when the silence is short).
  - New default style **`pop`** in `config.json`, plus a schema update.
  - Checked on the owner's 6-minute video: 469 cues, at most 2 words each; "bem-vindas" stays whole; pairs only after short words ("ao meu", "de crochê", "no fio", "a troca").
- **Add-on:** `presets/pop.json` (yellow, bold, thick outline, 96 px at 1080p); the style list puts "One word (pop)" ("Uma palavra (pop)") first, so it is the default; translations.
- **Samples regenerated** in `docs/local/teste-ass-2026-10-26/` (gitignored):
  - an `.ass` with one event per cue, the whole word yellow, centered at `\pos(960,860)`, and a pop of 70 % → 112 % → 100 % over 170 ms at the start only;
  - a 20 s FFmpeg burn-in, the alpha overlay, the `projeto-teste-pop.blend` project (Standard view transform);
  - a frame sequence of the pop on "BEM-VINDAS", and an FFmpeg vs Blender frame comparison (identical).
- **Plans:**
  - plan 04 §8 (feedback and what was done; the lesson that `\t` inside a multi-word line affects the whole line) and §9 (style catalog: phrase + active-word pop, karaoke, typewriter, slide, …);
  - new draft **plan 06** (Blender UX: one-click setup, entry points without the N key);
  - the plan 01 roadmap.

## Bug found while testing

The smoke test's range check decided "outside the range" by a caption's **start**, while the add-on uses the caption's **middle** (plan 02 §2c). With the owner's clip, a caption starting just before the range was correctly replaced and the test flagged it. The test now uses the midpoint rule.

## How it was tested

- Engine pytest: 60 passed. Add-on pytest: 35 passed. Ruff is clean.
- `blender_smoke.py --real` on a 30 s excerpt of the owner's video: 29/29 on Blender 4.2.23 and 5.2.3 (new check: the default style is pop). CI mode: 21/21.
- Visual: the frame sequence and the FFmpeg/Blender comparison (above).

## Pending / next steps

- The owner reviews the samples, then tests the add-on UI.
- Release engine 0.1.0.dev3 (tag after merge).
