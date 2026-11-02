# Plan 15 — Put the house in order

**Status:** in progress
**Date:** 2026-10-31
**Related:** `ROADMAP.md`, plan 12, plan 13, plan 14, ADR-008

## Goal

Everything that already works is in `main`, the docs tell one story, and the owner can send their list of corrections on a clean base.

## Context

The owner's view (2026-10-31): the plans had become messy, and "clone CapCut / InShot" was too vague to be a plan. Meanwhile the web editor has lived on one branch since step 31: PR #29 has been failing CI on lint, and 17 commits were not pushed.

## Proposed changes

1. **Direction, not a plan.** The CapCut / InShot idea moves to `AGENTS.md`; plan 13 is abandoned. Done in step 60.
2. **Roadmap by focus.** Now, next (the owner's corrections), parked, ideas. Done in step 60.
3. **Lint.** Fix the lint and format errors that fail CI. Done in step 60.
4. **Merge.** With the owner's approval: push the branch, wait for `ci`, merge #28, then #29.
5. **Access.** The owner closes the open points in plan 12.
6. **Phone test.** The owner tests the items listed in `ROADMAP.md`.

## Open questions

- How should the two PRs be merged? #28 is ready. #29 targets `main` and includes #28's commits, so it may need a rebase after #28 is squashed.

## Definition of done / how to test

- `ci` is green and both PRs are merged.
- `ROADMAP.md`, `PROJECT.md` and `chat-context.md` match the code.
- The access decision is recorded in plan 12 and ADR-024.

**Next task:** push and merge after the owner approves — tier: standard, effort: low — mechanical, with CI as the check.
