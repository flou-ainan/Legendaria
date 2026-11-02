# Step 34 — Round 2: timeline flicker, menu, local recovery, languages, logo

**Date:** 2026-10-27
**Agent/author:** Claude Code (Sonnet 5.5), with flou-ainan
**Related:** ADR-018, plan 08, plan 07

## What was done

- **Timeline flickering (bug):** with a drawer tab open the timeline redrew forever. Cause: the grid inside `.lower` had an implicit `auto` column, so the waveform's wide content made the column grow, the page narrowed again and wavesurfer redrew. Fix: `grid-template-columns: minmax(0, 1fr)`, `min-width: 0`, `scrollbar-gutter: stable`. The e2e test now samples the timeline for 1.8 s with a drawer open and the video playing, and fails if its size changes (it reproduced the bug before the fix: 921 ↔ 1334 px).
- **Logo and favicon:** `web/public/favicon.svg` and `logo.svg` (from `assets/brand`), in the tab, the header and the start screen.
- **Portuguese:** the language list showed "Português (pt)"; it now reads "Português (Brasil / Portugal)" and the list shows names only. Whisper has a single `pt` model for both.
- **Save and recover (ADR-018):**
  - IndexedDB copy of the work on every edit (`lib/recovery.ts`), with a `dirty` flag cleared when the server confirms.
  - Start screen "Continue where you left off". If the video moved, the screen says so and asks for it again; a replacement is accepted when the duration is within 0.5 s and the proportion within 1 %.
  - "Save now" and "Download a copy of the project" in the menu.
- **Menu bar** (`Menu.svelte`): File (open video, open project, close, save, download copy, export), panels on narrow screens, language. A hamburger under 900 px. Opening a `.legendaria.json` in the file browser opens its video (`/api/open` accepts the project path; `/api/browse` lists project files; `/api/state` returns the video `path`).
- **Interface language:** English and Brazilian Portuguese, chosen in the menu, remembered in localStorage, defaulting to the browser language.
- **CI mail:** run 40507344923 was the `workspace.py` formatting failure from step 33, fixed by the next commit; the later run passes.
- **UX study:** plan 08 maps the owner's PDF onto the current app and orders the next steps.

## Files touched

- Engine: `server.py`, `workspace.py`, `defaults/languages.json`, `tests/test_server.py`.
- Web: new `Menu.svelte`, `lib/recovery.ts`, `public/`; changed `App.svelte`, `Welcome.svelte`, `Browse.svelte`, `lib/editor.svelte.ts`, `lib/i18n.ts`, `lib/api.ts`, `app.css`, `index.html`, both locales, `e2e/smoke.mjs`, `lib/timeline.test.ts`.
- Docs: ADR-018, plan 08, `PROJECT.md`, `chat-context.md`.

## How it was tested

pytest (server), Vitest (video match rule), svelte-check, `npm run e2e` (flicker sampling, IndexedDB copy), screenshots of the menu on wide and narrow screens.
Not covered by a test: the relink screen in a browser (the match rule is unit-tested), restoring a `dirty` copy after a real crash.

## Pending

Plan 08 steps (contextual toolbar first); upload cleanup; touch dragging.
