# Step 52 — Desktop extras (plan 08, item 6)

**Date:** 2026-10-28
**Related:** plan 08, step 51

- **Ctrl+B** splits the subtitle under the playhead (`shortcuts.json` `split_ctrl_b`; `S` still works).
- **Search and replace** in the subtitle list: the search box filters the rows; "Replace all (n)" rewrites the matches in one undo step (`editor.replaceAll`, case-insensitive, plain text).
- **Right-click menu** on a timeline block: select it, then Split / Merge with next / Delete. Closes on click or Esc.
- Not done: the list is still inside the side drawer, not always visible (a layout change, left for the next step).
- Tests: svelte-check 0 errors, Vitest 11, `npm run e2e` ok. The new features have no e2e coverage yet and were not tried by hand in a browser.
