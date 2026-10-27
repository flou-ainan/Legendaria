# ADR 021 — Two playhead modes, and `settings.json`

**Status:** accepted (owner's request)
**Date:** 2026-10-27
**Related:** plan 08, ADR-015

## Context

The owner wants a draggable arrow on the timeline like Kdenlive's, to place each line precisely, and the mobile-editor behaviour (playhead fixed in the centre, timeline sliding under it, empty space before the start) so a swipe seeks. They also want important values in a JSON file that a Settings screen can expose later as basic and advanced.

## Decision

- **Both modes, same wavesurfer.js timeline.** `settings.playhead`: `auto` (default) picks the centred mode on touch screens (`pointer: coarse`) and the arrow elsewhere; `arrow` or `center` force one.
  - *Arrow:* a yellow triangle on wavesurfer's cursor line; dragging it seeks, and near an edge it scrolls the timeline.
  - *Centred:* half a screen of margin before and after the waveform (the regions sit inside the same wrapper, so they stay aligned); a per-frame loop keeps the scroll at `time × px/s` (read from the `<video>`, not from reactive state, ADR-015); a scroll that is not ours is a swipe and seeks. wavesurfer's own auto-centre is off in this mode.
- **`web/src/lib/settings.json`** with `basic` and `advanced` groups, read by `settings.ts`: playhead mode, snap distance (default 4 px), autosave delay, undo grouping and depth, start and maximum zoom. Edited by hand today; the Settings screen will read and write the same shape (and can keep user values in localStorage).

## Alternatives considered

- **Own timeline instead of wavesurfer's scroll:** more control, much more code; the margin trick on the wrapper works with the current regions.
- **One mode only:** the owner asked for both.

## Consequences

The centred mode is tested in a mobile-emulated browser, not on a real phone. Pinch zoom in that mode is still to do.
