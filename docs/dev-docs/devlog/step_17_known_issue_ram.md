# Step 17 — Known issue KI-001: freeze when loading `medium` from Blender

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What happened

The owner chose the `medium` model in Blender; RAM reached about 5.3 GB (attributed to Blender) and the PC froze, needing a hard reboot. That also interrupted this agent's session in the middle of stage 3a. The uncommitted 3a files survived on disk.

## What was done

- Gathered evidence after the reboot:
  - the model download had completed;
  - the journal ends right after it, with no OOM-killer entry;
  - the machine has 15 GiB of RAM and 2 GiB of swap.
- Created `docs/dev-docs/known-issues.md` with **KI-001**: evidence, hypotheses (most likely the model-load peak in the `flosub` child plus other heavy apps and little swap), a safe way to measure it (a memory-capped `systemd-run` scope with `/usr/bin/time -v`), and possible mitigations (RAM requirements per model, a pre-check, an explicit "Loading model" phase, a capped scope, a low-RAM compute type).
- Linked it from `PROJECT.md` and the dev-docs README.

Per the owner's request this is **recorded for later investigation**. Work continues on plan 03, stage 3a.

## How it was tested

Documentation only.
