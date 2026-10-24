# Step 05 — Brand kit (logo and key art)

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md (stage 0)

## What was done

- **Concept:** a sound wave flowing into subtitle lines. The owner iterated on it with Google Gemini; the references are in `assets/brand/source/`.
- **Flat symbol:**
  - Redrew it by hand as SVG strokes: 9 bars, the "Y" fusion of the outer arms into the center line, and 4 more text lines.
  - Fitted the geometry by overlaying the render on the reference.
  - Fitted the gradient (orange `#FF8A3D` → purple `#6418CB`) by sampling colors from the reference.
- **Main key art (the owner's choice):** the glowing version, recreated in SVG with the same geometry.
  - Glow made with filters, seeded particles, a "glass" shadow copy of the text lines, a light core, a horizontal streak, and a dark background.
  - Montserrat wordmark plus a tagline per language: "FREE SUBTITLES · CAPCUT STYLE" (en) and "LEGENDAS LIVRES · ESTILO CAPCUT" (pt-BR).
  - The Gemini image's tagline "Open Subtitler" was dropped (ADR-009).
  - Square hero (1024²) and wide banner (1280×640, also used as the social preview).
- **Flat kit:**
  - Symbol (color and mono), app icon.
  - Simplified small icon (4 bars, Y, 2 straight lines), readable at 16–32 px.
  - Montserrat lockups for light and dark backgrounds, `favicon.ico`, PNG renders.
- **Wordmark font:** Montserrat, matching the key art. The Nunito candidates were removed.
- **READMEs:** the glowing banner in the reader's language sits at the top of each.
- `assets/brand/README.md`: files, taglines, colors, typography, rules, how to regenerate.

## Files touched

- `assets/brand/**` (new)
- `README.md`, `README.pt-BR.md`, `docs/PROJECT.md` (tree and file map), plan 01 (stage 0 checklist), this file

## How it was tested

- Rendered every SVG with Inkscape and checked the results visually:
  - the flat symbol against the reference (overlay);
  - the key art side by side with the Gemini image;
  - the converted (text-to-path) banner, with filters intact;
  - the small icon at 16/32/64 px.
- No SVG contains a `<text>` element.
- Banner text has a right margin (its right edge is at x = 1164 of 1280).

## Pending / next steps

- The owner uploads `assets/brand/png/social-preview-en.png` under GitHub → Settings → General → Social preview (this cannot be done through the API).
