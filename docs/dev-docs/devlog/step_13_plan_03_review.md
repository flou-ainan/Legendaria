# Step 13 — Plan 03 (glossary + reviewer), ADR-010/011, roadmap update

**Date:** 2026-10-25
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **Looked at the owner's real output:** `flosub` on a 6-minute Portuguese crochet video, loaded into Kdenlive. Errors: "polieste" (Poliéster), "Nakley" (Enacles), "Bet" (Beth); 58 words had confidence < 0.5.
- **Prototypes on the owner's machine:**
  - The glossary as faster-whisper `hotwords` or `initial_prompt` fixed "Beth" and "Enacles" during transcription, with no LLM.
  - An LLM review through the local Ollama (OpenAI-compatible `/v1`), with `llama3.1:8b` and `qwen2.5-coder:7b` on 14 lines with a glossary: all target errors fixed, about 40–46 s. `llama3.1` also rewrote "perfeito→perfeita", which supports suggestions over auto-apply.
- **Owner decisions (2026-10-25):**
  1. The reviewer comes before the animations: plan 03 is accuracy, plan 04 the animations, plan 05 the API and web GUI.
  2. LLM: local OpenAI-compatible servers, with cloud optional.
  3. Review mode: suggestions **and** auto, configurable. Weak devices (CPU-only, mobile) must still benefit from the glossary without an LLM, which led to the device profiles.
  4. The `flosub` GUI is a local web interface now; a native window after the MVP, unless trivial.
- **Written:**
  - `plan_03_review_glossary.md` (evidence, three layers, modules, config, CLI, Blender UI, stages 3a–3c, open questions);
  - ADR-010 (review pipeline) and ADR-011 (core → access → clients);
  - drafts of plan 04 and plan 05;
  - the plan 01 roadmap and backlog (Kdenlive integration, native window);
  - `PROJECT.md`.

## Note: renumbered draft from another agent

A detailed "Plan 03 — CapCut-style animations" draft written by another agent (file dated 2026-10-26, not yet committed) was found in the working tree. To keep that work, it was renamed to `plan_04_capcut_animations.md`, its title changed to plan 04, and it replaced the short placeholder written in this step.

## How it was tested

Documentation only. The prototypes were ad-hoc scripts run outside the repository.

## Follow-up decision (2026-10-25)

Accepted fixes are **not** added to the glossary automatically. Every interface must offer "Add to glossary" (from a suggestion or from a selected caption), backed by `flosub glossary add`. Recorded in plan 03 §3.6 and ADR-010.

## Pending / next steps

- Stage 3a: glossary in the engine and CLI.
