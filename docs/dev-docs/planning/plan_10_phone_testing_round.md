# Plan 10 — Phone testing round (corrections from testing through ngrok)

**Status:** done (step 51)

The owner opened the editor on a phone through a tunnel (step 50) and reported five problems:

1. The file picker showed the server's disk. Through a tunnel it must be the device's own picker (the video is uploaded). `ui.remote` (page host is not localhost) selects it; on the same computer the server's browser stays.
2. Font previews in the Look menu did not render on mobile: native `<option>` ignores `font-family` there, and the fonts are not installed on a phone. Replaced by a list of buttons, with the bundled TTFs loaded into the page through the `FontFace` API the first time it opens.
3. Generate captions again: no warning, and the new cues showed only after a reload because the preview (`.ass`) was never refreshed after `editor.load`. Added a confirmation (it names the number of subtitles that will be lost) and `editor.refreshPreview()`.
4. Long press on a toolbar button shows what it does (`use:tip`; `title` does not show on touch).
5. Timeline: no subtitle text in the blocks, thin strip like InShot/CapCut (52 px, `settings.timelineHeight`), good for several tracks later.

**Next:** desktop extras of plan 08 (caption list always visible with search and replace, right-click menu, Ctrl+B split).
