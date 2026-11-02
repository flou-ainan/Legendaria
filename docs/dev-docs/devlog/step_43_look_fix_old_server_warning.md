# Step 43 — Look colours "not applied": an old server; heading; outdated-server warning

**Date:** 2026-10-27
**Related:** step 42, ADR-019

- **Owner's report:** colours and ALL CAPS did nothing. Cause: the owner's `flosub serve` had been started before step 42. The page (static files read from disk) was new, the Python code was old, so `clean_look` dropped the new keys on save and `/api/state` had no colour values in `base`. The engine itself was right (checked by hand and now in the e2e).
- **Guard:** `server.API_VERSION` (now 2) is sent in `/api/state`; the page compares it with `api.ts` `API_VERSION` and shows a red banner asking to restart the server when they differ. Bump both when the editor needs something new from the server.
- **Heading** "Edit all subtitles at once" / "Editar legendas globalmente" at the top of the Look menu.
- **e2e:** the Look test now sets the text and outline colours, the rectangle and turns ALL CAPS off, and checks the preview `.ass` (colour in the style, BorderStyle 3, lowercase text).

Tested: 132 pytest, svelte-check, Vitest 11, e2e.
