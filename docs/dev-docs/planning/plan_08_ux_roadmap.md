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
| 2. Contextual toolbar ≤ 5 | Not yet: the toolbar has 9 buttons and does not change with the selection. |
| 3. Orange cue track | Not yet: cue blocks are purple, the current one yellow. |
| 4. Batch vs one style | Not yet: one style per project. Needs per-cue style overrides in the project file (ADR-016 bump). |
| 5. Double-click + list | Done (step 33). |
| 6. Two layouts | Partly: one layout that reflows (drawer becomes a bottom sheet under 900 px). The menu is a hamburger on narrow screens. No separate mobile layout yet. |
| 7. Export top right | Done. |
| 8. 30-second test | Close: open or drop a video, press Transcribe, edit, export. Needs a real-use check. |

## Proposed order (each its own step, lean)

1. **Contextual toolbar:** nothing selected → Play, In/Out, Cut, Snap, Undo; a subtitle selected → Split, Merge, Delete, Edit text, Style. Max 5 visible, the rest in "more".
2. **Orange subtitle track** and a separate colour for the cut and the mark.
3. **"Generate captions" like CapCut:** a sheet with the source (all audio / voice only later), language, model and Generate. Today's Transcribe screen already has language and model; it becomes a sheet over the editor.
4. **Style sheet with "apply to all":** font, size, colour, position; needs per-cue overrides in the project file.
5. **Breakpoint at 1024 px** and a real mobile layout (bottom toolbar, bottom sheets with a slide transition, touch dragging and pinch zoom on the timeline).
6. **Desktop extras:** caption list always visible with search and replace, right-click menu, Ctrl+B split.

## Not now

Stickers, effects, multiple video tracks and animations from the study stay out until the subtitle flow is complete.
