# Step 26 — Native pop by font size (decided); storage format options

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **Decided (owner):** the native pop on Blender word strips animates `font_size` (plan 04 §11.4). It is implemented after the owner's manual test.
- **Aegisub license note** in plan 05: mostly 3-clause BSD (owner's research). Studying its design is free. If code is ever copied, check that file's license and keep its notice.
- **Storage format options** for transcript, style and edited document (plan 04 §11.5):
  - A: own JSON (today);
  - B: plain `.ass`;
  - C: extended `.ass` (Aegisub precedent);
  - D: layered, recommended;
  - E: project package.

  The decision is pending with the owner and will become an ADR.
- `PROJECT.md`: the pending decisions are updated.

No code changed.

## How it was tested

Docs only. Pre-commit passes.
