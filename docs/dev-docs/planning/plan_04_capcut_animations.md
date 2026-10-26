# Plan 04 — CapCut-style animations and style presets

**Status:** MVP look decided (§8, step 15); MVP subset done (§10, step 23); the rest is after the MVP.
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

## 6. `.ass` integration (added 2026-10-26)

Source: the owner's conversation about `.ass` (summary and checks: `references/ass_brainstorm.md`), proposed decision ADR-012. It answers open question 2 of §7 (karaoke rendering) with a second, exact rendering path.

### 6.1 One preset, two renderers

The preset JSON (§3.1) gains the fields `.ass` needs: font name, the four colors with alpha, outline, shadow, blur, alignment and margins, uppercase, and an animation block (`pop_scale`, `pop_ms`, `karaoke: fill|instant|none`, `fade_in_ms`). The **engine** turns a preset plus cues into `.ass`; the **add-on** turns the same preset into text-strip properties. The look is defined once.

### 6.2 Engine (`flosub`)

- `formats.to_ass(cues, preset, profile)`:
  - `[Script Info]` (PlayRes from the media), `[V4+ Styles]` from the preset, and `[Events]` with `\kf` (word durations in centiseconds), `\t` pops and `\fad`.
  - Profile `full` (CapCut look) or `basic` (bold, italic, color, outline, position only: **Kdenlive-compatible**, for the owner's workflow).
- `--format ass` on `transcribe` and `export`, plus `--ass-profile full|basic` and `--preset NAME`.
- `flosub overlay video.json --preset P` renders the subtitles alone to a transparent `video.overlay.mov` (FFmpeg `ass` filter on a transparent canvas, qtrle argb). Checked: real alpha, karaoke fill correct.
- `flosub burn video.mp4 --preset P` produces the final video with burned-in subtitles (FFmpeg `ass` filter; NVENC when available). This replaces the "fast burn-in" backlog item of plan 01.
- FFmpeg lookup per OS: PATH, the managed install (later), or a configured path. The styled path explains clearly when FFmpeg or libass is missing.

### 6.3 Blender

- **Editing:** the text strips stay the place to edit text, timing and position (plan 02).
- **Exact preview (optional toggle):**
  - "Exact preview" runs `flosub overlay` and puts the alpha `.mov` above the captions channel with `ALPHA_OVER`. Checked on 4.2.23 and 5.2.3.
  - "Refresh preview" after edits. The overlay is built from the **current strips**: strips → cues → `.ass` → overlay.
- **Native animations** (§3.3) remain for those who want to keyframe inside Blender.
- **Import `.ass` / `.srt`:** a light parser in the add-on (styles and dialogue; basic tags mapped to strip properties; override tags kept in a custom property, so a round trip does not lose them).
- **Export `.ass`** next to SRT/VTT.
- **Color management (done early, step 16):** generating captions switches the scene to "Standard" and says so; the panel warns and offers "Fix caption colors" when a scene is not on Standard. The default Filmic (4.2) and AgX (5.x) tone-map caption colors (yellow turned khaki in the check). This also affects the current add-on.

### 6.4 Bring your own subtitles: align an existing `.srt`

`flosub align video.mp4 --srt existing.srt`: transcribe with word timings, then align the SRT text to the transcribed words with a text diff (the same re-alignment as plan 03, `review/align.py`). The result is a transcript with the **user's text** and **word timings**, ready for CapCut styles and `.ass`. WhisperX/wav2vec2 forced alignment stays in the backlog as a fallback for difficult audio.

### 6.5 Stages

- **4a.** Preset schema v2 (shared by the engine and the add-on) and the preset gallery in the panel (§3–4); "Standard" view transform check.
- **4b.** Engine `.ass` export (`full` / `basic`), `overlay`, `burn`; FFmpeg lookup.
- **4c.** Blender: exact-preview overlay, native animations (`pop_in`, `karaoke`), `.ass` export.
- **4d.** Import: `.ass` / `.srt` into Blender; `flosub align --srt`.

## 7. Decisions that need the owner's input

1. **Look of the CapCut presets:** font size, colors (current-word highlight color, dim color), position, outline/shadow — propose defaults below or send reference screenshots.
2. **Karaoke rendering:** one strip per word vs. another approach; do keyframed strip properties work on your Blender 4.2.23/5.2.3?
3. **Emphasis words:** auto-detect from audio or manual list in a preset?
4. **Default preview in Blender** (ADR-012): native animated strips (editable, approximate), or the exact libass overlay (pixel-perfect, regenerated after edits)? Proposal: native for editing, the exact overlay as a toggle.
5. **Kdenlive:** is the `basic` `.ass` profile (Kdenlive-compatible) a priority, given the owner's current workflow?

Proposed CapCut defaults (to confirm):
- `font_size`: 76 (1080p base), `color`: white, `outline`: black, `position`: bottom-center slightly raised, `current_word_color`: yellow (`[1, 1, 0, 1]`), `dim_color`: half-opacity white.

Once you confirm the look, I'll implement plan 03 step by step, logging each step in `docs/dev-docs/devlog/` and updating `docs/PROJECT.md`.

## 8. Owner feedback on the samples (2026-10-26): the MVP look

After the first `.ass` sample (4-word blocks, karaoke fill, a pop on each word), the owner asked for:

1. **Smaller blocks:** **one word at a time**; two only when it makes sense or for compound words (guarda-chuva, micro-ondas).
2. **No style mixing:** the zoom must apply to the spoken word only. In the sample the whole line pulsed. Lesson: in `.ass`, an override tag such as `\fscx`/`\t` inside a line affects the layout of the whole line, so per-word animation inside a multi-word line needs one event (or one positioned layer) per word.
3. **No karaoke color sliding** for the MVP. Only the popped word, in the highlight color, and only one word on screen at a time.
4. Repeat the test with these changes.

**Done (step 15):**
- Engine style **`pop`**, the new default in Blender:
  - `max_words: 1`, measured in readable words: pieces Whisper glues on, such as "-vindas", never split off ("BEM-VINDAS").
  - `join_short: 3`: a word of up to 3 letters ("a", "de", "no", "que") takes the next one ("A BOLSA", "DE CROCHÊ").
  - `fill_gaps: 0.35`: no blank flashes between words.
  - Breaks at punctuation and pauses.
  - On the owner's video: 469 cues, at most 2 words each.
- `.ass` sample: one event per cue, the whole text in the highlight color (yellow), centered at `\pos(960,860)`, and a pop `\fscx70 → 112 → 100` over 170 ms at the start only. FFmpeg burn-in and the Blender alpha overlay give identical frames.
- Blender add-on: preset `presets/pop.json` (yellow, bold, outline, 96 px at 1080p), listed first as "One word (pop)". The pop animation inside Blender is still to do (§3.3).

## 9. Style catalog for later (owner, 2026-10-26)

Each is a preset (JSON) with an animation type, rendered by the engine to `.ass` (§6) and approximated in Blender:

| Style | Behavior |
|---|---|
| One-word pop | One word at a time with a pop (the MVP default, above) |
| Phrase + active-word pop | The whole short phrase visible; only the word being spoken pops and takes the highlight color, which reads comfortably |
| Karaoke | The phrase visible, color fills word by word (`\kf`) |
| Typewriter | Letters appear one by one |
| Slide | Captions enter from the left and leave to the right (`\move`) |
| More | Fade, bounce, emphasis words in another color, uppercase/lowercase variants, box/no box |

Adding a style must mean adding a preset plus, at most, one animation generator in the engine. The UI lists presets automatically.

## 10. MVP subset (stage 4-MVP, 2026-10-26)

What the MVP needs from this plan, before the owner's manual test and the alpha release. The rest of the plan (preset gallery, native animations in Blender, import, `align --srt`, the style catalog) stays for after the MVP.

### 10.1 Scope

- **Engine `.ass` export** (`--format ass` on `transcribe` and `export`):
  - the look of each style lives in the engine config, in a new `styles.<name>.ass` block. It is hackable JSON: font, size at 1080 px, bold, colors as RGBA floats (like the add-on presets), outline, shadow, position `[x, y from the bottom]`, uppercase, and `animation` (`none` or `pop` with `from` / `peak` / `ms`);
  - one `Dialogue` per cue, `\an5\pos(...)`, and the pop as `\fscx/\fscy` + `\t`, at the start only. No karaoke (owner, §8);
  - the canvas (`PlayResX/Y`) is the video size from `ffprobe`, or `--size WxH`, or 1920×1080 for audio. Sizes scale with the shorter side, so vertical videos get the same proportions;
  - the `full` profile only; `basic` (Kdenlive) after the MVP.
- **`flosub export` accepts a cues JSON** besides a transcript, so clients can export what the user edited (the Blender strips).
- **`flosub burn VIDEO`:**
  - burns the subtitles into a new video with FFmpeg's `ass` filter: `<name>.subtitled.mp4`, with progress events;
  - the subtitles come from `--subs FILE` (transcript, cues or `.ass`), by default `<name>.json` next to the video;
  - the encoder arguments live in config (`burn.video_args`, `burn.audio_args`);
  - FFmpeg comes from config `ffmpeg` or PATH, with a clear error when it is missing.
- **`flosub overlay SUBS --size WxH --fps F --duration S`:** renders the subtitles alone to a transparent QuickTime Animation `.mov`.
- **Blender:**
  - "Export ASS" next to SRT/VTT, made from the current strips;
  - **"Exact preview"**, an optional toggle following the §7.4 proposal:
    - it renders the strips through `flosub overlay` and puts the `.mov` above the captions with `ALPHA_OVER`;
    - it mutes the captions channel, so only the exact look shows; the strips stay editable;
    - "Remove exact preview" undoes it. After edits, the user runs it again;
    - Blender's normal render then gives the burned-in video.
  - The add-on presets scale fonts by the shorter side too, matching the engine.

### 10.2 Definition of done

- [x] `flosub export video.json --style pop --format ass` gives the approved look (yellow, one word, pop 70 → 112 → 100 % over 170 ms) — step 23.
- [x] `flosub burn` on the owner's clip; FFmpeg frame equals the Blender overlay frame — step 23 (18 of 336,000 caption-area pixels differ, all on chroma edges).
- [x] Blender: Export ASS and Exact preview on 4.2.23 and 5.2.3 (smoke test), pt_BR — step 23.
- [x] Tests (engine unit tests for the `.ass` writer, burn/overlay with FFmpeg when available; FFmpeg installed in Linux CI), docs — step 23.

## 11. Owner direction and Blender text capabilities (2026-10-26)

### 11.1 Direction

- **MVP focus (owner):** make what Blender itself can do work smoothly. A more robust Blender plugin, a fork of another program, or another editor is a decision for later.
- **Kdenlive is not part of the subtitle pipeline** (owner: it is only the video editor). The `basic` `.ass` profile (the subset Kdenlive's subtitle renderer understands) is **dropped**.
  - **Idea for after the MVP:** a Kdenlive fork dedicated to subtitles, with the full `.ass` feature set, because its interface beats Aegisub's and Blender's. Not evaluated yet. Kdenlive is a large C++/Qt code base, so the cost must be weighed against a dedicated UI (plan 05, a web GUI with a libass preview).

### 11.2 Capability test (step 24, Blender 4.2.23 and 5.2.3, headless renders)

| Capability | 4.2 | 5.2 | Note |
|---|---|---|---|
| Keyframes on `font_size`, `color`, `location`, `blend_alpha`, `transform.*`, `crop.*` | ✅ | ✅ | The `text` itself cannot be keyframed |
| **Pop by animating `font_size`** | ✅ | ✅ | Grows around the text's anchor; the position stays exactly in place |
| Pop by `transform.scale` | ✅ with `origin` = the text location | ⚠️ | The default origin (0.5, 0.5) moves the text toward the center. In 5.2 the origin is measured differently and no simple value kept the text in place, so `font_size` is the portable way |
| Keyframes follow the strip when it moves | ✅ | ✅ | Moving the strip 20 frames moved its keys 10 → 30 |
| `crop` on a text strip (karaoke-like reveal) | ✅ | ✅ | In pixels: needs the word's pixel bounds |
| Gaussian blur effect strip on a text strip | ✅ | ✅ | |
| Shadow offset, angle and blur | ✅ | ✅ | |
| Box roundness, line spacing | — | ✅ | 5.x only |
| Text measurement in the background (`blf.dimensions`) | ✅ | ✅ | Matching the strip's rendered size is not verified yet |

**Conclusion for the MVP:**
- These work natively and stay editable: one word at a time with a **pop** (`font_size` keyframes at each strip's start), fades (`blend_alpha`), slides (`location`), shadow blur and glow.
- These are hard without the `.ass` overlay: the active word highlighted inside a phrase (one strip per word positioned inline, which needs exact text measurement), karaoke fills, and per-letter effects.

### 11.3 Decisions on ADR-012's open questions

1. **Default preview in Blender:** postponed. The owner decides after testing the add-on more.
2. **Native animations in Blender:**
   - Owner: the pop should happen on the word strips themselves, in the one-word mode.
   - The test confirms this works with `font_size` keyframes: 70 → 112 → 100 % over 170 ms, which is about 4 frames at 24 fps.
   - **Planned for the MVP, after the owner's manual test feedback.**
3. **`basic` profile for Kdenlive:** dropped (§11.1).
4. **Import `.ass`/`.srt` and `flosub align --srt`:** postponed until the owner has tested more. **Agents must remind the owner when the MVP test round is over.**
5. **Duplicated look:**
   - Today `presets/<style>.json` (add-on, Blender text-strip properties) and `styles.<name>.ass` (engine) describe the same look twice, in different units (outline as a fraction of the font vs pixels; Blender's font vs Arial).
   - Fix after the MVP (stage 4a):
     - the engine owns one preset format;
     - the add-on reads it from the engine and translates it to strip properties, falling back to its bundled copy when the engine is missing;
     - each part still works alone (ADR-011).
   - Owner's view: the modular design (independent parts that work together or alone) is the right trade-off for an open, community-first, hackable project, and it will take shape gradually. The duplication was explained to the owner on 2026-10-26.
