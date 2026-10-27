# ADR 022 — Per-cue look overrides

**Status:** accepted (owner asked to follow plan 08)
**Date:** 2026-10-27
**Related:** ADR-016 (project file), ADR-019 (track look), plan 09

## Context

Plan 08 asks for "apply to all" versus "just this one" when styling subtitles. The project has one `look` for the whole track.

## Decision

- A cue in the project file may have an optional `look` object with the same keys and the same cleaning as the project `look` (`project.clean_look`). Empty or absent means the cue follows the track.
- Resolution order: style → track `look` → cue `look`, all through `ass.with_look`. `size` multiplies (a cue at 1.2 is 20 % bigger than the track), every other key replaces.
- In `.ass` each distinct resolved look becomes its own `Style:` line (`Default` for the track look, `Cue1`… for the others), so the preview, the `.ass` export and the burned MP4 agree.
- No project version bump: the field is optional and older readers drop it.

## Alternatives considered

- **Named styles in the project (a style list, cues refer by name):** closer to `.ass`, but the owner's flow is "change this one" or "apply to all", not managing a style library. A cue-level override covers it with less UI; a style list can come later with multiple tracks.
- **Inline ASS override tags per cue instead of extra `Style:` lines:** works for colours, but the rectangle, the position and the animation already come from the look, and extra styles keep each dialogue line short.

## Consequences

Remap after cuts must carry the cue's look (it does). Moving to several tracks later (plan 08) will put `look` on the track and keep it on cues.
