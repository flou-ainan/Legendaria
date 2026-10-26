# ADR 012 — `.ass` as the styled subtitle format and the high-fidelity renderer

**Status:** accepted for the MVP subset (step 23): `.ass` export (`full` profile), `burn`, `overlay`, and the exact preview as an optional button in Blender, following the plan 04 §7.4 proposal. Still open: the `basic` (Kdenlive) profile, import, and whether the exact preview should become the default (the owner decides after the manual test).
**Date:** 2026-10-26

## Owner input (2026-10-26)

See plan 04 §11:
- for the MVP, what Blender does natively must work smoothly; the pop goes on the word strips with `font_size` keyframes (planned after the manual test);
- the `basic` (Kdenlive) profile is dropped, because Kdenlive is not part of the subtitle pipeline;
- the default preview and import / `align --srt` wait for the owner's tests;
- the duplicated look is unified after the MVP (stage 4a).

## Context

CapCut-style captions need per-word color fills and scale "pops". Blender's text strips have one style per strip, so they can only approximate this (one strip per word, keyframes). The owner also edits in Kdenlive, whose subtitle track is `.ass`-based, and dislikes Aegisub's UI. `.ass` plus libass already renders karaoke fills, `\t` animations, outlines and blur everywhere (FFmpeg, mpv, VLC, HandBrake). The checks are in `references/ass_brainstorm.md`.

## Decision (proposed)

- **One style definition, two renderers:**
  - A style preset (JSON, ADR-006) describes the look and the animation once.
  - The engine turns it into `.ass` (styles plus override tags from word timings).
  - The add-on turns it into text-strip properties (and, for animations, strips and keyframes).
- **Engine:**
  - `--format ass`, with profiles `full` (every tag, the CapCut look) and `basic` (the subset Kdenlive understands).
  - `flosub burn` renders the final video with FFmpeg's `ass` filter (NVENC when available).
  - `flosub overlay` renders the subtitles alone to a transparent video (qtrle `.mov`).
- **Blender:**
  - Editing stays on text strips: text, timing, position.
  - An optional **"exact preview" overlay** (the libass-rendered alpha `.mov` above the footage, `ALPHA_OVER`) shows the final look, and is regenerated after edits.
  - `.ass` import and export.
- **Color management:** the add-on checks the scene's view transform and offers to switch it to "Standard", so colors are not tone-mapped.

## Alternatives considered

- **Blender text strips only:** fully editable, but they cannot match the CapCut look (no multi-color strip, no blur, limited animation).
- **Our own renderer:** no reason when libass already does this, is standard, and is fast (6 s of overlay rendered in about 1 s).
- **Python libass bindings:** extra native dependency; FFmpeg already ships libass.

## Consequences

- FFmpeg with libass becomes a dependency of the styled path. It is optional: plain captions work without it, and the installer or engine must locate FFmpeg on each OS.
- Two previews can disagree (strips vs overlay). The overlay is the source of truth for the final render.
- An `.ass` parser in the add-on (basic tags only) for import.
