# Step 14 — `.ass` research folded into plan 04 (ADR-012 proposed)

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **Summarized the owner's Gemini conversation about `.ass`** in `references/ass_brainstorm.md`: the format's capabilities, the ecosystem (libass, FFmpeg, Aegisub, Kdenlive, Blender), the ideas for Legendária, and corrections.
- **Checked the key claims on the dev machine:**
  - FFmpeg 4.4 has libass (`ass` / `subtitles` filters) and the alpha encoders `qtrle`, `prores_ks`, `png` and `vp9`.
  - Built an `.ass` from the owner's real cues: `\kf` karaoke fill, `\t` pop, a Montserrat bold style, 1080×1920. Rendered it onto a transparent canvas to qtrle argb: a real alpha channel, and the progressive fill renders mid-word.
  - Blender **4.2.23 and 5.2.3**: the `.mov` as a movie strip with `ALPHA_OVER` composites correctly over a color strip.
  - **Found:** the default view transform (Filmic / AgX) tone-maps VSE colors (yellow → khaki). Video work needs "Standard". This affects the current add-on's caption colors too.
- **Plan 04 extended** with §6:
  - one preset → `.ass` (engine) and strips (add-on);
  - engine `to_ass` with `full` and `basic` (Kdenlive-compatible) profiles, plus `flosub overlay` and `flosub burn`;
  - the Blender exact-preview overlay, `.ass`/`.srt` import, `.ass` export and the view transform check;
  - `flosub align --srt`, by transcription plus text alignment, reusing plan 03's aligner;
  - stages 4a–4d and two new owner questions.
- **ADR-012 (proposed):** `.ass` as the styled format and the libass high-fidelity renderer.
- **Plan 01 backlog:** "fast burn-in" moved into plan 04; WhisperX noted as the fallback for `align`.

## How it was tested

Ad-hoc scripts in the scratchpad (FFmpeg render, alpha check, headless Blender render on both versions). No repository code changed.

## Pending / next steps

- The owner answers plan 04 §7 (preview default, Kdenlive profile priority, look).
- Plan 03 (glossary + reviewer) is still next in line.
