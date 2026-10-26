# Step 25 — Blender 5.2 minimum (ADR-013), pop by scale vs font size, web editor brainstorm

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **ADR-013 (accepted, owner):** Blender 5.2 LTS is the minimum; 4.x support is dropped. The code, CI and docs change after the owner's manual test.
- **Tests on 5.2.3**, in plan 04 §11.4:
  - `transform.origin` is not in canvas coordinates, so a pop by scale needs an origin computed per strip;
  - `font_size` renders in whole pixels, with about 1 px of center jitter between sizes, which does not show in a 4-frame pop.
  - Recommendation: `font_size` for the pop. The owner decides when the native pop is implemented.
- **Plan 05:** the owner's brainstorm on a full web subtitle editor beyond the MVP: why web instead of a Kdenlive fork, libass in WebAssembly for an exact preview, a data model inspired by `.ass` and Aegisub, phones.
- `PROJECT.md`: the ADR table and the pending items.

No code changed.

## How it was tested

Render scripts in the scratchpad on Blender 5.2.3 (480×270): bounding boxes of a yellow text strip at several locations and origins with `transform.scale` 1.5, and at `font_size` 40.0–41.0 and 44.8.
