# Step 03 — Round-2 decisions: installer, macOS, docs site, languages, workflow

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md

## What was done

- Recorded the owner's answers in plan 01, section 6 (decisions 9–15):
  - Installer: the "Install engine" button in the add-on comes first; native installers or a bundled Blender come later.
  - macOS: CPU only; an Apple Silicon backend is left to contributors.
  - Docs site: MkDocs Material.
  - Portuguese and English transcription are first-class in the MVP.
  - Burn-in through Blender only; the fast FFmpeg path goes to the backlog.
  - Python 3.11 pinned through `uv`.
- Added **stage 0 (project foundation)** to plan 01: community files, CI, templates, branch protection, name and logo.
- Added a **backlog** section and moved the open questions to section 9 (name, translation goal).
- Added the "Install engine" flow and pt/en checks to the MVP stage 2 and to the definition of done.
- New **ADR-008** (contribution workflow) and its row in `PROJECT.md`.
- Researched the availability of the name "Open Subtitler" (see the summary below).

## Name research summary

- "Open Subtitler": free on PyPI; on GitHub, only this repository uses it. Risk: easy to confuse with OpenSubtitles.org, a large brand in the same field. `opensub` is used by opensub.in.
- Checked alternatives (PyPI 404 means the name is free):
  - `legendaria`: free on PyPI; no subtitle product found.
  - `substrip`: free; no product found.
  - `wordcue`: free; unrelated small repos only.
  - `kaption`: free on PyPI, but a GitHub repo "Kaptiono" is a local Whisper subtitle generator (too close).
  - `subforge` and `captionforge`: taken on PyPI.

## Files touched

- `docs/dev-docs/planning/plan_01_mvp_engine_blender.md`
- `docs/dev-docs/decisions/ADR-008-contribution-workflow.md` (new)
- `docs/PROJECT.md`, this file

## How it was tested

Documentation only.

## Pending / next steps

- The owner picks the name; then the logo; then stage 0.
