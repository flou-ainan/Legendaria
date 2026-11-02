# Plan 09 — Style for one subtitle, or for the whole track

**Status:** done (step 45)
**Related:** plan 08 item "Batch vs one", ADR-019, ADR-022

## Goal

The owner's study: a style change hits every subtitle, or breaks away for one. Today the Look menu edits the whole track (the project `look`).

## Design

- **Project file:** each cue may carry an optional `look` with the same keys as the project `look` (ADR-022). Absent means "like the track". No version bump: older files load unchanged, and the server already ignores unknown keys inside a cue.
- **Layers of look:** style (config) → track (`project.look`) → cue (`cue.look`). `size` multiplies at each level, the others replace.
- **`.ass`:** one `Style:` line per distinct look (`Default` for the track, `Cue1`, `Cue2`… for cues that differ); each cue's position, box and animation come from its own look.
- **Editor:** with a block selected, the Look menu has a switch "This subtitle | Whole track". In "This subtitle" every control writes the cue's `look`; the shown values are cue → track → style. Two buttons: **Apply to all** (move this cue's overrides to the track and drop those keys from every cue) and **Reset** (clear this cue's look). Split keeps the look on both halves; merge keeps the first one's. The timeline marks cues with their own style.
- Cut remap keeps each cue's look.

## Steps

1. Engine: `Cue.look`, project load/save and schema, remap, `to_ass` per-cue styles. Tests.
2. Web: types, editor commands (`setCueLook`, `applyToAll`), Look menu switch, split/merge, timeline mark. e2e.
3. Docs: ADR-022, devlog, PROJECT.md, chat-context.

## Not in this plan

Several subtitle tracks (plan 08 "Later: subtitle tracks"), animations per cue.

**Next:** plan 08, mobile layout (breakpoint 1024 px, bottom sheets, pinch zoom) — tier: standard, effort: medium.
