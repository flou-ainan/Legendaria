# ADR 007 — Cross-platform target: Linux, macOS, Windows 10+

**Status:** accepted
**Date:** 2026-10-24

## Context

The tool should reach end users on every desktop OS. Development starts on Linux with an NVIDIA GPU.

## Decision

- Officially supported targets: **Linux, macOS, Windows 10+**. The MVP ships on Linux first, but its code is written portably from day one.
- Rules:
  - `pathlib` everywhere.
  - `subprocess` with argument lists, never `shell=True`.
  - Per-OS dirs through `platformdirs`.
  - A single helper for venv layout differences (`bin/` vs `Scripts/`).
  - NVIDIA library loading has Linux (`ctypes` preload) and Windows (`os.add_dll_directory`) branches.
- Acceleration:
  - NVIDIA CUDA on Linux and Windows.
  - CPU (int8) everywhere as the fallback.
  - macOS starts on CPU, and the transcriber has a small backend interface so an Apple Silicon backend can be added later (plan 01, open question 2).
- CI (phase 3) runs the engine tests on all three OSes.

## Consequences

- Some features have to be checked on three OSes before a release.
- Mac users get slower transcription until an Apple Silicon backend lands.
