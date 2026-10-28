# Step 33 — The owner's first round of corrections

**Date:** 2026-10-27
**Agent/author:** Claude Code (Sonnet 5.5), with flou-ainan
**Related plan:** planning/plan_07_web_editor.md
**Related decision:** decisions/ADR-017-opening-files-in-the-browser.md

## What was done

The owner tested the MVP and sent 8 corrections.

1. **No path needed:** `flosub serve` takes an optional video. Without one the server starts "empty" and the browser shows a start screen. Routes that need a video answer 409 until one is open.
2. **Open a file or drop a video:** "Choose a file…" opens a file browser dialog backed by `/api/browse` (the video is opened in place); dropping a file uploads it to the data folder. Why they differ: ADR-017.
3. **Drop-down lists:** the model list comes from the catalog and shows the size and whether it is downloaded; the language list is `defaults/languages.json` (a user copy in the config dir wins); the style list was already there.
4. **Glossary tools:** a Glossary tab with the active glossary, new, add a word or `wrong -> right`, import a `.txt` and export, next to the review. New module `workspace.py` holds these and the browser; routes under `/api/glossary`.
5. **Live snapping + magnet:** the block now sticks to nearby targets while it is dragged (not only on release), with a white guide line at the target. A magnet button in the tool row under the video turns snapping on and off (shortcut M). Snapping is also unit-tested; the browser test drags an edge and checks the guide and the final value.
6. **Layout:** the Kdenlive-like structure (video on top, timeline below) with CapCut/InShot-style big icon buttons: a tool row under the video (play, in, out, cut, split, magnet, undo, redo), an inspector for the selected block, the timeline. Buttons are touch-sized and the drawer becomes a bottom sheet on narrow screens. Touch dragging on the timeline has not been tested.
7. **Double-click edits:** double-clicking a block selects it and focuses its text box (Esc leaves the box so the shortcuts work). Splitting stays in the tool row and the inspector (shortcut S). A click selects the block and moves the playhead to it.
8. **The right-hand list is optional:** the subtitle list is now a tab of the drawer (Subtitles, Glossary, Cuts, Export), closed by default. The result of every edit is seen in the video and on the timeline at once.

## Files touched

- New: `engine/legendaria_engine/workspace.py`, `defaults/languages.json`; `web/src/components/{Welcome,Browse,Toolbar,Inspector,Glossary,Drawer}.svelte`, `web/src/lib/ui.svelte.ts`; ADR-017, this step.
- Changed:
  - engine: `server.py`, `cli.py`, `tests/test_server.py`;
  - web: `App.svelte`, `Player.svelte`, `Timeline.svelte`, `Transcribe.svelte`, `CueList.svelte`, `lib/{api,editor.svelte,player}.ts`, both locales, `shortcuts.json`, `e2e/smoke.mjs`, `app.css`;
  - docs: `PROJECT.md`, plan 07, `chat-context.md`.

## How it was tested

- Engine: 127 pytest passed (new: starting without a video, browse, open by path and by upload, glossary add/import/export).
- Web: `svelte-check` 0/0, Vitest 6, build, and `npm run e2e` (updated: starts with no video, opens the file through the browser dialog, live snap and guide, magnet off, double-click to edit, cut, undo, glossary add + apply all, SRT export).
- Screenshots at 1400 px and 390 px wide checked by eye.
- `pre-commit run --all-files` passes.

## Pending / next steps

- The owner keeps testing and sending corrections.
- Known gaps: touch drag on the timeline, drive list on Windows in the file browser, cleaning old uploads, `.ass`/`.srt` import, "add selected word to the glossary".
