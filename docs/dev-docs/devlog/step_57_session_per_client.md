# Step 57 — One session per browser (plan 11, item B)

**Date:** 2026-10-28
**Related:** ADR-023, plan 11

- `server.py`: the global `server.session` became `server.sessions` (client id → `Session`), with the id taken from the `legendaria_client` cookie (set by `Handler.end_headers` on the first response). The startup video opens lazily per browser. `API_VERSION` is 5 (also in `web/src/lib/api.ts`).
- Tests: `test_server.py` keeps a cookie per server like a browser; new tests for two browsers getting different ids and for opening a video in one browser not changing the other. 139 pytest pass.
- e2e: the node-side `project()` read now goes through the editor page's request context (it carries the cookie), and the phone-sized page reuses the same cookie. `npm run e2e` ok.
- **Not done:** a warning when two browsers open the same project file (they still share the file on disk). Not tried with a real phone and a computer at the same time.
