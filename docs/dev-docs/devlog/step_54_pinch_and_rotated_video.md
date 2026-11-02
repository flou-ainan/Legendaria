# Step 54 — Pinch zoom jump and squashed letters on 9:16 video

**Date:** 2026-10-28
**Related:** step 47 (pinch zoom), step 49 (tall video)

Reported by the owner after testing through ngrok on a phone.

- **Pinch jumped the video ahead (zoomed all the way out):** on touch screens a drag on the timeline pans by seeking, and the pan handler also reacted to the moves of the two pinch fingers. Fully zoomed out one pixel is many seconds, so the video jumped far ahead. The pan now follows only the finger that started it and does nothing while two fingers are down.
- **Squashed letters on 9:16 video:** for a phone video recorded sideways with a rotation flag, Chrome reports the stored (unrotated) size in `requestVideoFrameCallback`; JASSUB took it as the video size and made its canvas buffer transposed (measured 440x248 for a 248x440 box, in about half of the loads), so libass drew stretched text. `Player` now wraps the video's frame callback to report `videoWidth`/`videoHeight` (the displayed size). Measured with Playwright on a clip with a rotation flag: 4 of 4 loads right (before: 2 of 3 wrong).
- e2e: updated for step 53 (the subtitle list is open by default on a wide screen, then closed to keep the rest of the run).
- Tests: svelte-check 0 errors, Vitest 11, `npm run e2e` ok. The pinch fix is not covered by a test and was not tried on a real phone; the rotated-video fix has no automated test (the test clips are WebM, which carries no rotation flag).
