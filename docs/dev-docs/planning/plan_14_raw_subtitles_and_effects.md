# Plan 14 — Raw subtitles plus effects

**Status:** draft; build after the owner approves ADR-025
**Related:** ADR-025, ADR-016, ADR-022, plan 13, `ass.py`, `cues.py`

## Goal

Cues are always normal subtitle lines with precise word timings. Pop per word, word highlight and letter colour are **effects** chosen per track (and per cue), drawn by the engine as `.ass` animation. SRT/VTT are always the clean text.

## Steps (each leaves the app working)

1. **Effects module.** `engine/legendaria_engine/effects.py` with the kinds `none` and `word_pop` (today's pop, reproduced) and a registry; `ass.py` calls it instead of `animation_tags`. Golden `.ass` tests: the same output as today for pop.
2. **Config.** An `effects` section in `defaults/config.json`; styles get `effect` (the old `animation` is still read). Schema updated.
3. **Grouping decoupled.** The `pop` style groups into short lines (2–3 words) instead of single words; one-word grouping remains available as a layout option. Words are always kept in the cues.
4. **New kinds.** `word_color` (karaoke) and `letter_color`, with fallback timing when words are missing. Golden tests.
5. **Project file v2.** `effect` on the track and per cue; v1 files load unchanged. Round-trip tests.
6. **Web.** An "Effect" picker in the Look menu (whole track / this subtitle, like the look), with the preset parameters that matter (colour, speed). Preview stays live through JASSUB.
7. **Docs.** READMEs (how to add a preset in JSON), PROJECT.md, a short "write an effect kind" guide for contributors.

## Open questions for the owner

- Should `pop` keep one word per screen (short lines, one word visible at a time) as CapCut's pop does, or show the line with the current word popping? The `show: current | line` option covers both; which is the default for `pop`?
- Do you want presets editable in the app (colour picker per effect) or only in the JSON for now?

## Not in scope

Per-letter physics, particles, 3D, and effects that need video compositing; anything that cannot be written as `.ass`.
