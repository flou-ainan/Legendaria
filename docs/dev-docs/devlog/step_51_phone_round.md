# Step 51 — Phone testing round (plan 10)

**Date:** 2026-10-28
**Related:** step 50, plan 10

- **Client's files:** `ui.remote` is true when the page host is not localhost/127.0.0.1. Then "Choose a file…", File ▸ Open video and relinking use the browser's own picker (`pickFile`) and upload the video (progress shown). On the same computer nothing changes.
- **Fonts on mobile:** the Look menu's font `<select>` became a button + list; each row is drawn in its own family. `lib/fontfaces.ts` loads the bundled TTFs with `FontFace` on first open.
- **Regenerate captions:** the sheet asks "Replace all subtitles?" (with the count) before running. Bug found: the preview showed the old cues until a reload, since only a save refreshed it; `App` now calls `editor.refreshPreview()` after loading the new project.
- **Long-press tips:** `lib/tip.ts`, an action on every toolbar button (touch/pen only; the mouse keeps the native tooltip). It also swallows the click that ends the press.
- **Timeline:** blocks carry no text (✦ stays for an own style); the strip is 52 px (`settings.json` `timelineHeight`).
- Tests: svelte-check 0 errors, Vitest 11, `npm run e2e` (font list + FontFace loaded, empty block text, strip height, the confirmation dialog). Not tested on a real phone: the upload picker, the long-press tip, the regeneration itself (only the dialog).
