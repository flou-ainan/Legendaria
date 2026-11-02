# Step 48 — Bottom sheets: lower height, the video stays visible

**Date:** 2026-10-27
**Related:** step 47, plan 08

Owner's correction: the sheet covered the video, so the subtitle changes could not be seen. On narrow screens the Look sheet and the drawer are now at most 44 % of the screen high (they scroll inside); while one is open the page gets room below it, scrolls so the video is at the top, and the video with its toolbar is pinned (sticky) with a 30 vh maximum height. `ui.look` and `ui.sheet` (in `ui.svelte.ts`) tell the page a sheet is open. e2e: the video is fully above the sheet and the sheet is under 45 % of the screen.
