# Step 05 — Brand kit (logo)

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md (stage 0)

## What was done

- **Concept:** a sound wave flowing into subtitle lines. The owner explored it with Google Gemini; the raster references are in `assets/brand/source/`.
- **Vectorization:**
  - Redrew the symbol by hand as SVG strokes: 9 bars, the "Y" fusion of the two outer arms into the center line, and 4 more text lines.
  - Fitted the geometry by overlaying the render on the reference.
  - Fitted the gradient (orange `#FF8A3D` → purple `#6418CB`) by sampling colors from the reference.
- **Kit in `assets/brand/`:**
  - Symbol: full color and mono.
  - App icon, plus a simplified small icon (4 bars, Y, 2 straight lines) that stays readable at 16–32 px.
  - Lockups for light and dark backgrounds, in two candidate fonts (Montserrat SemiBold, Nunito ExtraBold), with the text converted to paths.
  - 1280×640 social preview, `favicon.ico`, PNG renders.
  - `README.md` with usage rules, color tokens and how to regenerate everything.
- **READMEs:** the logo is now at the top of both, and switches automatically between the light and dark GitHub themes (`<picture>`). Nunito is used until the font is chosen.

## Files touched

- `assets/brand/**` (new)
- `README.md`, `README.pt-BR.md`, `docs/PROJECT.md`, plan 01 (stage 0 checklist), this file

## How it was tested

- Rendered every SVG with Inkscape and checked the results visually: the symbol against the reference (overlay), the lockups on light and dark backgrounds, the small icon at 16/32/64 px.
- Checked that the lockup and social SVGs contain no `<text>` elements (everything converted to paths).

## Pending / next steps

- The owner picks the wordmark font. The unused lockup and social files are then removed.
- Upload `png/social-preview-*.png` as the repository's social preview (GitHub → Settings → General → Social preview; this cannot be done through the API).
