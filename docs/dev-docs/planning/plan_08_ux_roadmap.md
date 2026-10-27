# Plan 08 — UX roadmap (CapCut-style, responsive, lean)

**Status:** long-term goal, delivered feature by feature
**Source:** owner's study `docs/local/Capcut-Svelte-Ux-Responsivo.pdf` (local only, not committed) and the CapCut screenshots (auto captions: "Generate from" Video / Voice; Model; Generate).
**Related:** plan 07 (web editor), ADR-015

## What the study asks for

1. **Three fixed zones:** player on top (always visible), timeline in the middle, a toolbar at the bottom.
2. **Contextual toolbar, 5 icons at most:** nothing selected = global actions; a subtitle selected = Split, Style, Animation, Delete.
3. **Subtitle track in orange**, above the video track.
4. **Batch vs one:** a checkbox "apply to all captions" decides whether a style change hits every subtitle or breaks away for one.
5. **Text edit:** double-click on the block, or a plain list.
6. **Same stores, two layouts:** one logical state, a mobile layout (< 1024 px: stacked, bottom sheets) and a desktop one (Kdenlive-like: side bin, wide timeline, fixed inspector).
7. **Export** button always visible, top right.
8. **30-second test:** a person uploads a video and gets subtitles with no tutorial.

## Where we are

| Idea | State |
|---|---|
| 1. Three zones | Done: video, then timeline, then the toolbar under the video. The toolbar sits between player and timeline, not at the very bottom. |
| Owner corrections after step 36 | Done (step 37): only the selected block moves/resizes (touch scrolling), a magnet that follows the pointer, Undo/Redo first, Solar icons. |
| 2. Contextual toolbar ≤ 5 | Done (step 36): nothing selected = Play, In, Out, Cut, Look; a block selected = Play, Split, Merge, Delete, Look. Snap, Undo and Redo stay as a small utility group. Esc or a click on the empty waveform deselects. |
| 3. Orange cue track | Done (step 40): cues orange (current brighter, selected lighter), cuts grey-blue, in/out mark blue. The separate row above the video track waits for a multi-track timeline. |
| 4. Batch vs one style | Not yet: one style per project. Needs per-cue style overrides in the project file (ADR-016 bump). |
| 5. Double-click + list | Done (step 33). |
| 6. Two layouts | Partly: one layout that reflows (drawer becomes a bottom sheet under 900 px). The menu is a hamburger on narrow screens. No separate mobile layout yet. |
| 7. Export top right | Done. |
| 8. 30-second test | Close: open or drop a video, press Transcribe, edit, export. Needs a real-use check. |

## Priority round 3 (owner request, 2026-10-27; before the items below)

1. **Subtitle look quick menu:** a "Look" button under the video opens a small panel with a size slider, a vertical-position slider, two presets (Top, Bottom) and a font drop-down. Stored in the project as an optional `look` object (`font`, `size` multiplier, `y`), so it is undoable, autosaved and applied by the preview and by the export alike (ADR-019).
2. **More fonts:** a curated set of ~19 open-licence families (SIL OFL) from the owner's font folder, bundled in `engine/legendaria_engine/fonts/` with a catalogue (`fonts.json`: family, file, category). The server serves them to the preview and passes them to FFmpeg's libass (`fontsdir`), so the burned video matches without installing anything.
3. **Easy translations:** every language is one JSON file in `web/src/locales/`, found automatically (no code to register), with its own name inside (`_name`), missing keys falling back to English, a guide for translators, and a test that reports missing and unknown keys.
4. **Mobile toolbar and spacing:** the tool row scrolls sideways in one line (like mobile editors), smaller icons and tighter spacing under 900 px.

## Then, proposed order (each its own step, lean)

1. ~~Contextual toolbar~~ (done, step 36).
2. **Orange subtitle track** and a separate colour for the cut and the mark.
3. **"Generate captions" like CapCut:** a sheet with the source (all audio / voice only later), language, model and Generate. Today's Transcribe screen already has language and model; it becomes a sheet over the editor.
4. **Style sheet with "apply to all":** font, size, colour, position; needs per-cue overrides in the project file.
5. **Breakpoint at 1024 px** and a real mobile layout (bottom toolbar, bottom sheets with a slide transition, touch dragging and pinch zoom on the timeline).
6. **Desktop extras:** caption list always visible with search and replace, right-click menu, Ctrl+B split.

## Not now

Stickers, effects, multiple video tracks and animations from the study stay out until the subtitle flow is complete.

## After the MVP

- **Interactive tutorial** (a guided first run). The permanent tips were removed from the screen to save space (step 36): click a block to select it, double-click edits its text, drag a block or its edges, Ctrl + wheel zooms. They move into the tutorial.
