# Step 39 — Playhead fixes

**Date:** 2026-10-27
**Related:** step 38, ADR-021

## What was done

Owner's report: the seek line moved with the timeline while dragging (right only on release), things at the left of it were not drawn, and the arrow was inside the timeline.

- Cause of the missing blocks: the margins added to wavesurfer's wrapper in step 38 broke its visible-range calculation. Removed; the empty start is now a `transform` shift of the wrapper while the playhead is in the first half screen.
- Cause of the jitter: the playhead was wavesurfer's cursor, moving with the scrolling content. It is now an overlay positioned per frame, fixed in the middle in centred mode.
- The arrow lives in a strip above the waveform and the line crosses the blocks, outside the shadow DOM.
- Centred mode pans with its own pointer drag.

## Tested

svelte-check, build, `npm run e2e` (arrow drag seeks; touch-emulated page: playhead stays in the middle at 3 s and at 0 s, dragging seeks). Screenshot checked. Not tried on a real phone.
