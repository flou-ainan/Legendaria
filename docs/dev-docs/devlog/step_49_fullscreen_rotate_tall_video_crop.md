# Step 49 — Full screen after rotating, tall video above a sheet

**Date:** 2026-10-27
**Related:** steps 44, 48

- **Rotating a phone in full screen** left the video small and the subtitle canvas misplaced. I could not reproduce it in emulated Chromium (it worked), so the sizing was made robust instead of guessed: the full-screen box is `position: fixed; inset: 0` and the video fills it by percentage (not `100vw`/`100vh`, which can be stale right after a rotation); `Player.refit()` re-lays out JASSUB's canvas on `fullscreenchange`, `resize`, `orientationchange` (three times, up to 500 ms later). e2e: after a CDP rotation to landscape the video fills 800×390 and the canvas stays inside. **Still to confirm on the owner's phone.**
- **Tall video with a bottom sheet open:** the video sits in a `.viewport` of at most 34 vh; a video taller than that is cropped, not shrunk. It keeps the bottom (where subtitles usually are), or the top when the selected subtitle (or the track) is above the middle (`look.y > 0.5`), so the foot is cut. JASSUB's canvas is inside the same `.frame`, so it moves with the video. Short (landscape) videos are unchanged. e2e uses a 360×640 clip: bottom shown by default, top after the Top preset, the viewport fits above the sheet.
- Fixed a console error: `refit` waited for JASSUB's renderer before resizing.
