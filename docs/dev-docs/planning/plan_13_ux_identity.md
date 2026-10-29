# Plan 13 — UX identity: InShot / CapCut on the phone, Kdenlive on the desktop

**Status:** draft (owner, 2026-10-29: "the essence is missing from the plans"). Research first, build after the owner approves the target.
**Related:** plan 08 (UX study, now a reference), ADR-015, ADR-021, ROADMAP

## The idea

One editor state and two skins, each copying a tool people already know:

- **Phone (under 1024 px): clone the InShot / CapCut experience.** The goal is that someone who has used either app finds everything where they expect it.
- **Desktop (1024 px and up): a Kdenlive feel, shortcuts included.** Panels, a monitor, a wide timeline, and the Kdenlive keymap.

Today the app is a good editor with a responsive layout, but it does not yet feel like either. This plan names the gap and the order to close it.

## Step 0 — Research (before any code)

The owner sends screenshots or screen recordings of the exact flows to copy (Telegram is enough); I write them up as a short reference in `references/` (what is on screen, where, what a tap does). Without this I would be copying from memory.

- CapCut / InShot: opening a project, the bottom tool strip and its sub-strips, the text/caption flow, auto captions, styles, export sheet.
- Kdenlive: default layout, project bin, monitors, timeline tools, the default keymap (verify each key in Kdenlive's own settings, not from memory).

## Phone: gaps to check against CapCut / InShot (to confirm in step 0)

1. **Bottom tool strip as the main navigation:** big icons with labels that open a sub-strip (Captions → Edit, Style, Split, Delete…) and a back arrow to the parent strip. Ours is one flat row.
2. **Top bar:** back/close at the left, Export at the right (resolution and frame rate sheet), Undo / Redo near the video.
3. **Fixed playhead with a sliding timeline, pinch zoom** (done), plus a play button and the time beside it, and a "main track" with clip handles you drag to trim.
4. **Caption track as chips on the timeline** that you tap to select and drag the edges of; a long press to move; a tap on empty space to deselect.
5. **Style presets as a carousel** (tap a thumbnail to apply), then fine controls; "apply to all" as a toggle.
6. **Text edit by tapping the caption on the video** (inline edit) as well as from the list.
7. **Auto captions as a first-run action** ("Auto captions" button when the project is empty).
8. **Touch feel:** 44 px targets, haptic or visual feedback, 60 fps scrolling, safe areas, no page bounce, screen awake while playing.

## Desktop: Kdenlive feel

1. **Layout:** project bin (media and the caption list) on the left, monitor in the middle, properties (Look, glossary) on the right, timeline across the bottom; panels can be resized, and later hidden or docked.
2. **Timeline tools:** selection, razor (cut at the playhead or on click), spacer; snapping toggle; zoom with Ctrl + wheel; ruler with timecode.
3. **Keymap:** a Kdenlive preset in `shortcuts.json` (J / K / L shuttle, I / O, Space, razor, frame and second stepping, Home / End, Ctrl+Z family, and so on), selectable as "Legendária" or "Kdenlive". Our current keys that clash (`x` cut range, `s` split, `m` snap) get reassigned in that preset.
4. **Menus:** File / Edit / View / Tools / Settings bar like Kdenlive, with the shortcut shown next to each item.

## Order (proposal)

1. Research (step 0), then the owner picks the first screens to match.
2. Phone: bottom tool strip with sub-strips + top bar (1–2), since it changes how everything else is reached.
3. Desktop: Kdenlive keymap preset (cheap, high feel), then the panel layout and menu bar.
4. Phone: caption chips, inline edit, style carousel (4–6).
5. Touch feel pass on a real phone (8).

## Not in scope

Copying CapCut/InShot branding, artwork or assets, and their effects, stickers, music and templates. We copy the interaction patterns, not the content.
