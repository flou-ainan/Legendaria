# Plan 04 — CapCut-style animations and style presets

**Status:** proposed (draft — awaiting owner input on the look)
**Renumbered:** written by another agent as "plan 03" on 2026-10-26. It became plan 04 when the owner put the glossary/reviewer first (plan 03, ADR-010), and its content is kept as written. References below to "plan 03" mean this plan.
**Date:** 2026-10-26
**Builds on:** plan 02 (done, steps 09–12), ADR-002, ADR-005, ADR-006

## 1. Goal

After plan 02 (captions as editable text strips in Blender's VSE), plan 03 makes the captions feel like CapCut's auto captions:

- **Style presets gallery:** several JSON presets (CapCut, minimal, karaoke, bold highlight) the user can pick in the panel. Each preset drives font size, color, outline, shadow, position, wrap width, and an animation type.
- **CapCut animations:** pop-in entrance, current-word highlight (karaoke) that follows the speech, and emphasis-word colors.
- Everything driven by JSON configs/presets — adding a new preset must not require code changes.

## 2. Requirements

| # | Requirement | Where |
|---|---|---|
| A1 | The user chooses a style preset in the panel (default = `captions`). | panel |
| A2 | A preset is a JSON file; user overrides live in `<config dir>/presets/`. | presets |
| A3 | Animation types: `none`, `pop_in`, `karaoke`. | engine + add-on |
| A4 | Karaoke highlights the current spoken word; the word timings already stored on strips (step 10) are reused. | add-on strips |
| A5 | Emphasis words can be colored differently within a cue. | engine cues |
| A6 | Existing strips keep working when no animation preset is chosen (backward compatible). | add-on |
| A7 | UI in English and pt_BR; new strings translated. | i18n |

## 3. Design

### 3.1 Style presets (add-on side)

Extend each preset JSON (`presets/captions.json`, `presets/subtitles.json`) with an `animation` key:

```json
{
  "version": 1,
  "font_size": 76,
  "location": [0.5, 0.2],
  "animation": "karaoke",
  ...
}
```

New presets are added as files in `presets/` (e.g. `presets/karaoke.json`, `presets/minimal.json`, `presets/bold.json`). `strips.load_preset(style)` already supports user overrides in the config dir, so no code change is needed to pick a preset file — only to read the new `animation` key and to expose the preset list in the panel.

### 3.2 Cue data (engine side)

The cues JSON v1 (`<stem>.cues.json`) already stores `Cue.words` (per-word timings). Plan 03 adds, optionally:

- `emphasis`: list of word indices to highlight (color) differently, from a user-editable emphasis list or auto-detected (e.g. loud/long words).
- Animation intent lives in the add-on preset, not in the engine, so the engine contract (cues v1) stays stable.

### 3.3 Animations (add-on side)

| Type | Behavior | Implementation |
|---|---|---|
| `none` | Static cue strip (current behavior). | Unchanged. |
| `pop_in` | Cue scales/fades in at its start and out at its end. | One text strip per cue; animate via Blender strip properties/keyframes where supported. |
| `karaoke` | One text strip per word, timed to each word; the current word is highlighted (color), previous words dimmed, future words hidden. | One strip per word using the stored word timings; words laid out inline on the same line/channel. |

Open question (needs owner input): how to render per-word highlighting in Blender's VSE. A text strip is monochrome, so karaoke needs one strip per word (positioned inline) — or the highlight can be approximated by cycling strips. Confirm the preferred approach and whether keyframed strip properties work on your Blender versions (4.2.23 / 5.2.3).

## 4. Changes

- **[NEW] `blender_addon/legendaria/presets/karaoke.json`**, `minimal.json`, `bold.json` (CapCut-inspired defaults).
- **[CHANGE] `strips.py`:** read preset `animation`; create one strip per cue (`none`/`pop_in`) or one strip per word (`karaoke`); apply per-word colors.
- **[CHANGE] `panel.py`:** add a style-preset selector (defaults to `captions`).
- **[CHANGE] `properties.py`:** expose the chosen preset/animation in scene settings.
- **[CHANGE] `i18n.py` + `locales/pt_BR.json`:** translate new UI strings.
- **Tests:** preset loading, per-word strip timing, animation types, i18n coverage.

## 5. Definition of done

- [ ] Panel lets the user pick a style preset; default is `captions`.
- [ ] `none`/`pop_in`/`karaoke` animations produce correct strip timing.
- [ ] Karaoke reuses stored word timings; current word highlighted.
- [ ] New presets are pure JSON (no code change to add one).
- [ ] pt_BR translations complete; i18n test passes.
- [ ] Engine cue format unchanged (cues v1 still valid).
- [ ] Docs: `PROJECT.md` file map updated, devlog step written.

## 6. Decisions that need the owner's input

1. **Look of the CapCut presets:** font size, colors (current-word highlight color, dim color), position, outline/shadow — propose defaults below or send reference screenshots.
2. **Karaoke rendering:** one strip per word vs. another approach; do keyframed strip properties work on your Blender 4.2.23/5.2.3?
3. **Emphasis words:** auto-detect from audio or manual list in a preset?

Proposed CapCut defaults (to confirm):
- `font_size`: 76 (1080p base), `color`: white, `outline`: black, `position`: bottom-center slightly raised, `current_word_color`: yellow (`[1, 1, 0, 1]`), `dim_color`: half-opacity white.

Once you confirm the look, I'll implement plan 03 step by step, logging each step in `docs/dev-docs/devlog/` and updating `docs/PROJECT.md`.
