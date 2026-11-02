# Step 55 — The end of the video is reachable in centred mode

**Date:** 2026-10-28
**Related:** step 38 / ADR-021 (centred playhead), step 54

Reported by the owner on a phone (voice message): with the playhead centred it was impossible to see the end of the video.

- **Cause:** the playhead stays in the middle and the timeline scrolls under it, but the scroll stops at `scrollWidth - view`, so the last half screen of the waveform could never reach the centre. The start already had empty space (a shift to the right); the end had none.
- **Fix:** `follow()` also shifts the waveform to the left by the amount the scroll cannot cover, so the playhead can sit on the very last frame over empty space.
- Test: `e2e/smoke.mjs` seeks to the end on the touch page and checks the playhead is on the waveform's last edge. It fails without the fix (194.8 vs 368.8 px) and passes with it. Not tried on a real phone.
