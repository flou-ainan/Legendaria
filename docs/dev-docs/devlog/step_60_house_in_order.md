# Step 60 — Reorganize the roadmap, fix the lint errors

**Date:** 2026-10-31
**Agent/author:** Claude Code (Opus 5.5)
**Related plan:** planning/plan_15_house_in_order.md

## What was done

- `ROADMAP.md` is now ordered by focus: now, next (the owner's corrections), parked, ideas.
- The CapCut / InShot idea moved to "Product direction" in `AGENTS.md`; plan 13 is abandoned and plan 14 is parked.
- Plan 15 created. Plan 12 got its open points on access.
- `chat-context.md` brought up to date, including the 2026-10-29 documentation work.
- Fixed the CI lint and format failures: import order and line wrapping in `server.py`, unused variable in `test_server.py`.

## Why

The owner found the plans messy and wants to tie together what works before sending corrections. These failures are what fails `checks` on PR #29.

## Files touched

`AGENTS.md`, `docs/PROJECT.md`, `docs/dev-docs/ROADMAP.md`, `docs/dev-docs/chat-context.md`, plans 12–15, `engine/legendaria_engine/server.py`, `engine/tests/test_server.py`.

## How it was tested

- `pre-commit run --all-files`, the CI lint step, passes; pytest: 140 passed. Vitest (11 passed) and `svelte-check` (0 errors) were run before these edits; no web file changed.
- CI has not run on this yet: nothing is pushed.
- Plain HTTP check (plan 12): a throwaway `flosub serve` on `127.0.0.1` with `--allow-host legendaria.test`, opened in headless Chromium through that name. The subtitle preview rendered at 0:05.

## Pending / next steps

See plan 15.
