# ADR 025 — Raw subtitles plus effects (the look-and-motion layer)

**Status:** proposed (owner idea, 2026-10-29; to approve before building)
**Date:** 2026-10-29
**Related:** plan 14, ADR-012 (`.ass` + libass), ADR-016 (project file), ADR-019, ADR-022

## Context

Today a *style* (`pop`, `subtitles`, `captions`) bundles three different things: how words are **grouped** into cues (`pop` makes one-word cues), the **look** (font, colour, box…) and the **motion** (`animation`, only `pop`). Because grouping is baked into the cues, the "pop" project has no real subtitle text: its SRT is one word per cue, and changing the effect means re-transcribing or regrouping.

CapCut does it the other way round: the subtitle is always a normal, precisely aligned text line, and "effects" (pop per word, colour the current word, colour letters) are a visual layer on top of it.

## Decision

Three separate layers, from the data to the picture:

1. **Cues (the raw subtitle).** Normal lines (sentence-sized, `subtitles`-like grouping), each with its `words` (start, end, text) kept as the atomic alignment. SRT and VTT export these as they are, whatever the effect. This is the document (ADR-016).
2. **Look.** Font, colour, outline, shadow, box, position (unchanged; the Look menu and ADR-019/022 overrides).
3. **Effect.** How the line moves and highlights over time. It never changes cue text or timing; it only changes how the `.ass` is drawn.

An effect is a named preset in the config (JSON, hackable) that points at a **kind**, a small function in the engine, plus parameters:

```json
"effects": {
  "none":      { "kind": "none" },
  "pop-word":  { "kind": "word_pop", "from": 70, "peak": 112, "peak_ms": 90, "ms": 170, "show": "current" },
  "karaoke":   { "kind": "word_color", "color": [1, 0.85, 0, 1], "show": "line" },
  "letters":   { "kind": "letter_color", "color": [1, 0.85, 0, 1], "show": "line" }
}
```

- The kinds start as `none`, `word_pop` (a word at a time, scaled in; today's pop), `word_color` (whole line shown, the spoken word takes the colour) and `letter_color` (the colour sweeps through the letters of the spoken word). Adding a kind is one function in `effects.py` plus an entry in a registry dict; adding a preset is only JSON.
- A kind turns `cue + words + look` into `.ass` events (ASS override tags such as `\t`, `\fscx`, `\k`/`\kf`, or one event per word). The live preview (JASSUB) and the burned export use the same `.ass`, as today.
- **Without word timings** (a cue the user retyped, an imported SRT) the engine spreads the cue's time over the words, or letters, by length. The effect still works, only less precisely.
- A project stores `effect` (a preset name or an inline object) on the track; a cue may override it, next to its own `look` (ADR-022).
- **Styles stay as bundles** (`pop`, `subtitles`, `captions`): `{ layout, look, effect }`. `pop` becomes "short lines + the pop-word effect" instead of one-word cues. The old `animation` field is read as an effect for existing configs.
- **Project file** goes to version 2: `effect` is added, cues from a version 1 project keep working (their words may be missing; the fallback above applies). A converter is not needed beyond defaults.

## Alternatives considered

- **Keep effects as part of the style (today):** simplest, but grouping stays in the cues and SRT is wrong for pop.
- **Write effects as raw ASS override strings in the config:** very hackable, but users must know ASS and a typo breaks the render; named kinds with parameters are safer, and a raw-tags kind can be added later.
- **Do the effects in the browser (canvas) and in FFmpeg separately:** two implementations that drift; one `.ass` rendered by libass in both places is already proven (plan 07 spike).

## Consequences

- Cleaner mental model for users and contributors: text, look, effect.
- More work than renaming: regrouping (`cues.py`) is decoupled from the style, `ass.py` gets an `effects.py` beside it, the Look menu gets an "Effect" picker, the project format gets a version bump, and golden `.ass` tests are needed.
- Existing `pop` projects keep their one-word cues until regenerated.
