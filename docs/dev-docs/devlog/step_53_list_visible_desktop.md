# Step 53 — Subtitle list visible on desktop (plan 08, item 6)

**Date:** 2026-10-28
**Related:** step 52, plan 08

- On screens of 1024 px or more the side drawer opens on the subtitle list from the start (`ui.panel` initial value). The ✕ still closes it and the header buttons reopen it. Narrow screens keep the closed bottom sheet.
- With this, plan 08 item 6 (desktop extras) is complete.
- Tests: svelte-check 0 errors, Vitest 11, `npm run e2e` ok. Not checked by eye in a desktop browser.
