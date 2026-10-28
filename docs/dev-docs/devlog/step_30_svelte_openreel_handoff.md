# Step 30 — Svelte 5 chosen, OpenReel dissected, chat-context hand-off

**Date:** 2026-10-27
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_07_web_editor.md

## What was done

- **ADR-015:** the web editor front end is Svelte 5 + Vite + TypeScript. The owner chose it after comparing it with Vue 3 and React. It records the player rule (no frame-rate time in reactive state), snapshot undo, MIT for the web UI, and the build notes from the spikes.
- **READMEs (en + pt-BR):** they now describe the browser editor (cut, edit, live final look, export SRT/VTT/ASS or burned video). The roadmap points to plan 07, and the Blender add-on is marked frozen. This builds on the owner's own uncommitted edit of `README.md`.
- **OpenReel dissection:** `references/openreel_dissection.md`. It adopts patterns, with no code copied:
  - undo with auto-grouping;
  - pixel-threshold snapping (plus word boundaries);
  - a data-driven shortcut table in JSON;
  - zoom-at-cursor and follow-playhead;
  - a versioned, validated project file;
  - property-based tests.
  - It also lists what is not adopted, and why.
- **New hand-off policy:** `docs/dev-docs/chat-context.md` holds a lean summary of the owner ↔ agent conversation plus the last two complete replies. It is updated on request and after long stretches of work. Added to `AGENTS.md` (the reading order and the rule) and `docs/dev-docs/README.md` (layout, contents, privacy). The first snapshot is written.
- `PROJECT.md` (stack, ADR table, tree, in progress) and plan 07 are updated.

## Files

- New:
  - `docs/dev-docs/decisions/ADR-015-web-frontend-svelte.md`;
  - `docs/dev-docs/references/openreel_dissection.md`;
  - `docs/dev-docs/chat-context.md`.
- Changed: `README.md`, `README.pt-BR.md`, `AGENTS.md`, `docs/dev-docs/README.md`, `docs/PROJECT.md`, `docs/dev-docs/planning/plan_07_web_editor.md`.

## How it was tested

Docs only:
- the links were checked;
- the OpenReel findings were read from the cloned source (`action-history.ts`, `clip-manager.ts`, `keyboard-shortcuts.ts`, `Timeline.tsx`, `portable-project.ts`).
