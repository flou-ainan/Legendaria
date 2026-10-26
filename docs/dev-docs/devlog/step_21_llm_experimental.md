# Step 21 — LLM reviewer marked experimental; plan bookkeeping

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **Owner decision:** after the step 19 findings, the LLM reviewer (layer 3) is **experimental**.
  - The default is now `review.llm.enabled: false`. Users opt in with `flosub review --llm` or the config (`true` / `auto`).
  - The CLI help, the config schema, ADR-010, plan 03 (status and §7) and the CHANGELOG say "experimental".
  - Test: the LLM is off by default; the auto-mode degradation test now opts in explicitly.
- **Plan bookkeeping**, so the plans match reality before the remaining MVP work:
  - plan 01: definition-of-done items verified in steps 07–11/15/18 are checked, with references. "Edit a strip, then export SRT" stays open for the owner's manual test.
  - plan 02: status text updated (the follow-ups are plans 03, 04 and 06).
- **Remaining MVP work (owner: "execute what is pending"):**
  1. plan 03 stage 3c (Blender: glossary, review, Add to glossary);
  2. the MVP subset of plan 04 (engine `.ass` export with the approved one-word pop, `flosub burn`, exact preview in Blender);
  3. then the owner's manual test, the README update, an alpha release and PyPI.

## How it was tested

`uv run pytest`: 91 passed. Ruff is clean.
