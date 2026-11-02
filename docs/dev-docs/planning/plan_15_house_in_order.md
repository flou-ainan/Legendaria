# Plan 15 — Put the house in order

**Status:** done (2026-11-02)
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
4. **Merge.** Done 2026-11-02 with the owner's approval: pushed, `ci` green, #28 squashed, `main` merged into the branch (7 doc conflicts, kept the branch's newer versions), #29 squashed.
5. **Access.** Decided on 2026-11-02 (ADR-026, plan 12). Implementation is plan 12, not part of this plan.
6. **Phone test.** The owner tests the items listed in `ROADMAP.md`.

## Open questions

- None left. (The two PRs were merged as above.)

## Definition of done / how to test

- `ci` is green and both PRs are merged (done).
- `ROADMAP.md`, `PROJECT.md` and `chat-context.md` match the code.
- The access decision is recorded in plan 12 and ADR-026 (done).

**Next task:** the owner's hands-on test of network access (plan 12), then their list of corrections — tier: standard, effort: medium — fixes against a written design.
