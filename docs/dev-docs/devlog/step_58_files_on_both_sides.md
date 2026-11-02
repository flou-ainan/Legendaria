# Step 58 — Files from the computer or the phone, results to either (plan 11, item D)

**Date:** 2026-10-28
**Related:** plan 11, step 51 (device picker), step 57

- **Open:** when the page is opened from another device (`ui.remote`), the start screen, the relink prompt and the File menu offer both "this device" (the picker; the video is uploaded) and "the computer's files" (the server's file browser; nothing is uploaded). On the computer itself nothing changes.
- **Save:** after an export finishes, a phone sees "Save to this device", a download of `<video>.edited.<ext>` through the new `GET /api/output?name=...` (the file also stays on the computer). The route only serves `<stem>.edited.mp4|srt|vtt|ass` of the open video, anything else is a 404. `_file` got an `attachment` option (`Content-Disposition`).
- Tests: a pytest for the route and its limits (140 pass), svelte-check 0 errors, Vitest 11, e2e ok. The remote-only buttons are not covered by e2e (the test page is `127.0.0.1`) and none of this was tried on a real phone.
