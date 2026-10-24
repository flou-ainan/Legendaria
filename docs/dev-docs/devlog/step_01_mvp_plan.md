# Step 01 — MVP plan from the origin brainstorm

**Date:** 2026-10-23
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md
**Commit(s):** a9f7743

## What was done

- Read the origin brainstorm with Gemini. The mobile part was ignored, as requested.
- Wrote plan 01: the `opensub` engine (faster-whisper → JSON with words) plus a Blender add-on (editable text strips, SRT/VTT export).
- Recorded ADR-001 (faster-whisper), ADR-002 (Blender VSE) and ADR-003 (engine as an external process).
- Updated the project map with the architecture, the stack and the decisions.
- Checked the environment: Blender 4.2.0 (wrong: only a dangling symlink, see step 09), Python 3.10.12, faster-whisper 1.2.1, ctranslate2 4.6.1, cuDNN 9.1 and cuBLAS 12.1 (pip), ffmpeg 4.4.2, RTX 2070 Super 8 GB.

## Why

To turn an exploratory conversation into an executable plan, and to fix the problems in Gemini's sample code (listed in plan 01).

## Files touched

- `docs/dev-docs/planning/plan_01_*.md`, `docs/dev-docs/decisions/ADR-001..003`, the project map, this file

## How it was tested

Documentation only; nothing to run.

## Pending / next steps

- Answer the open questions (done in step 02).
