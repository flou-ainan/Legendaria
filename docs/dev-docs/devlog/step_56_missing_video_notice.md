# Step 56 — Tell at once when the video is gone

**Date:** 2026-10-28
**Related:** ADR-018 (relinking a moved video), step 34

Owner report: the "The video was moved or removed" screen only appeared after clicking the file name; before that the editor showed a player that could not load.

- `Player` listens to the `<video>` error event and asks the server for the first byte of `/api/media`. If the server says no, it calls `onMissing`; a failure caused by a codec the browser lacks (the file is there) is left alone.
- `App` then closes the video and passes `missing` to `Welcome`, which opens straight on the relink prompt (when this browser has a copy of the work).
- Test: `e2e/smoke.mjs` renames the video, reloads and waits for the prompt. It times out without the change and passes with it. Not tried on a real phone.
