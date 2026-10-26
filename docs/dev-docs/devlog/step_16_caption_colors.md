# Step 16 — Caption colors: Standard view transform (owner's first Blender run)

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What happened

The owner ran the add-on in Blender 5.2: it worked end to end, the interface feels complex but is workable, and the "pop" captions appeared **white instead of yellow**.

## Diagnosis

- The installed extension has `presets/pop.json`, and a strip created through it has `color = (1, 1, 0, 1)`. The add-on was right.
- The scene used Blender 5's default **AgX** view transform, which tone-maps the sequencer output. The same strip rendered as **(199, 193, 108)** with AgX and **(255, 255, 0)** with Standard. Over video, the pale yellow reads as white.
- This was already noted in plan 04 §6.3 during the `.ass` research (step 14); it is fixed now because it affects real use.

## What was done

- `operators.use_exact_colors()` and `colors_are_exact()`. Every run that creates captions (generate, re-apply style, regenerate range) goes through `finish_strips()`, which switches the scene to **Standard** and reports "Color management set to Standard…".
- A new operator, **"Fix caption colors"**, and a warning box in the panel when the scene is not on Standard (for existing projects).
- pt_BR translations.
- Smoke test: it starts from AgX/Filmic and checks that generating switches to Standard.
- **Notes:**
  - plan 06 gets the owner's idea of a **launcher** that opens Blender with a preconfigured project, plus the first-use feedback;
  - plan 04 §6.3 is marked as done early.

## How it was tested

- Reproduced with the owner's installed extension, enabled temporarily in a headless run without saving preferences, and rendered with AgX and with Standard.
- Add-on pytest: 35 passed. `blender_smoke.py --real`: 30/30 on Blender 4.2.23 and 5.2.3 (the icon check covers the new `COLOR` icon).

## Also checked: ai-memory

`ai-memory doctor`: the project coordinate is exact, and 6 Claude Code sessions were captured for `flou-ainan-legendaria`. An empty `RENDER` project appeared, from an agent session started inside the video folder; it is harmless.
