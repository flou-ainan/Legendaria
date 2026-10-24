# ADR 003 — Engine as an external process, talking JSON

**Status:** accepted
**Date:** 2026-10-23 (accepted 2026-10-24)

## Context

Blender ships its own Python. Installing faster-whisper, CTranslate2, and the CUDA libraries into it is fragile and breaks with every Blender update.

## Decision

The engine (`engine/`) is a standalone Python package with its **own venv** and the `opensub` command. The add-on runs it with `subprocess.Popen`:

- Progress arrives as JSON lines on stdout.
- The result is a versioned JSON transcript file with segments and words with timings.

## Alternatives considered

- **Installing the dependencies into Blender's Python:** fragile, and a cuDNN crash would take Blender down with it.
- **A local HTTP server:** useful later (mobile/cloud), but too much for the MVP.

## Consequences

- The engine also works on its own as a CLI, and a future API can reuse it.
- An engine crash cannot crash Blender.
- The JSON format becomes a contract and carries a version (`"version": 1`) and a published JSON Schema.
- Timestamp formatting is duplicated in the engine and the add-on, because the add-on cannot import the engine.
- Someone has to create the venv: the developer in dev, and the installer or the add-on for end users (plan 01, open question 1).
