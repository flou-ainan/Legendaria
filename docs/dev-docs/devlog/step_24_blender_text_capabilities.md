# Step 24 — Blender text-strip capabilities; owner input on ADR-012

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **Headless tests** on Blender 4.2.23 and 5.2.3 of what text strips can do for CapCut-style animation. The results are a table in plan 04 §11.2. In short:
  - every style and transform property can be keyframed, but not the text itself;
  - a **pop by `font_size` keyframes stays in place on both versions**. A pop by `transform.scale` needs an origin at the text location on 4.2 and does not stay in place on 5.2;
  - keyframes follow a moved strip;
  - `crop` works on text strips, so a karaoke-like reveal is possible;
  - a blur effect strip on text and shadow blur both work;
  - `blf.dimensions` works in the background.
- **Owner direction:**
  - the MVP makes what Blender does natively work smoothly;
  - Kdenlive is not in the pipeline, so the `basic` `.ass` profile is dropped;
  - a Kdenlive fork for subtitles is an idea for after the MVP.
- **ADR-012 open questions:** recorded in plan 04 §11.3. Two are postponed until the owner's tests: the default preview, and import / `align --srt`. The native pop on word strips is planned after the test feedback. Unifying the look is post-MVP stage 4a. `PROJECT.md` lists the pending decisions so that any agent reminds the owner.

No code changed.

## Files

`docs/dev-docs/planning/plan_04_capcut_animations.md` (§11), `docs/dev-docs/decisions/ADR-012-ass-styled-format.md`, `docs/PROJECT.md` (§7), this step.

## How it was tested

Probe and render scripts were run in the scratchpad, not in the repository, on both Blender versions. They rendered 480×270 frames of a yellow text strip and measured the bounding box of the yellow pixels at base size, `font_size` 60, `transform.scale` 1.5 with different origins, and with `crop.max_x`. A montage confirmed the crop reveal and the blurred shadow.
