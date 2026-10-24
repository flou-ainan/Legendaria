# Step 07 — Stage 1: the transcription engine (`flosub`)

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md (section 4.4)
**Related decisions:** ADR-001, ADR-003, ADR-006, ADR-007

## What was done

- **Package** `engine/`:
  - Distribution `legendaria`, import `legendaria_engine`, console script `flosub`.
  - hatchling build, `uv.lock` committed, dev Python pinned to 3.11 (`.python-version`).
  - Extras: `cuda` (NVIDIA cuBLAS/cuDNN wheels, Linux/Windows only) and `test`.
- **Modules** (details in `PROJECT.md`):
  - `paths`: per-OS dirs, with env overrides.
  - `config`: defaults → user `config.json` → CLI values; validation that names the bad key; model catalog plus user `models.json`.
  - `events`: JSON-lines or human (tqdm) reporter.
  - `schema`: transcript v1 dataclasses.
  - `formats`: SRT / VTT, with ms-exact timestamps that keep counting past 24 h.
  - `models`: catalog listing; download through `huggingface_hub.snapshot_download` with throttled `model_download` events.
  - `cuda_libs`: makes the pip NVIDIA libraries loadable.
  - `transcriber`: `Backend` protocol plus `FasterWhisperBackend`, with GPU→CPU fallback.
  - `cli`: `transcribe`, `export`, `models list|download`, `config show|path`, and `--progress auto|json|human`.
- **JSON Schemas** for config, models and the transcript; the defaults are validated against them in the tests.
- **32 pytest tests**, needing no GPU or network.
- **`tools/project_map.py`** generates the `PROJECT.md` file map. Docstrings were added so every public function has a summary.
- `ruff.toml`: `legendaria_engine` declared first-party (import sorting from the repo root).

## Deviations from the plan

- The NVIDIA libraries are an optional extra, not a base dependency: they weigh about 1 GB and CI, CPU-only and Mac users do not need them.
- Linux uses a single self re-exec with `LD_LIBRARY_PATH` instead of `ctypes` preloading. It is simpler and is guaranteed to work.
- Progress mode is chosen automatically from whether stdout is a terminal (`--progress` overrides it), instead of an opt-in `--human` flag.
- The GPU→CPU fallback covers failures during decoding too, not only at model load.

## Bugs found by real runs and fixed

1. The download progress class crashed: a disabled `tqdm` has no `unit` attribute. It now tracks bytes itself.
2. Download events reported `total: 0`, because Hugging Face grows the total while it discovers files. The live total is now used, with the catalog size as a fallback. Events are throttled to one every 0.25 s.
3. Unexpected exceptions printed a traceback instead of an `error` event. `main` now catches everything.
4. A missing `libcublas` surfaced only when decoding started, so the `auto` mode did not fall back. Fixed (see the deviations above), and covered by `test_transcriber.py`.

## How it was tested

- `uv run pytest`: 32 passed. Ruff check and format are clean.
- Real runs on the dev machine (RTX 2070 Super, driver 595, Linux Mint), with public-domain LibriVox clips (not committed):
  - **English**, 38 s, `small`, GPU fp16: language `en` (0.995), 10 segments with per-word timings, about 4.5 s end to end including model load. JSON, SRT and VTT written.
  - **Portuguese**, 106 s (17th-century poetry), `small`, GPU: language `pt`, about 4.5 s. Archaic words are partly misheard, as expected with `small`; larger models are one download away.
  - **CPU**, `tiny`, `--device cpu`: int8, 38 s of audio in about 2.5 s.
  - **Download**: `models download tiny` emits `log`, then throttled `model_download` events with the correct total, then `finished` and `done`.
  - **Proof the CUDA fix is needed:** with it disabled, `libcublas.so.12 is not found`. In `auto` mode the run now warns and finishes on the CPU.

## Pending / next steps

- Stage 2: the Blender add-on (it reads these JSON events and the transcript).
- The Windows and macOS code paths (DLL dirs, no CUDA) are only exercised by CI unit tests so far; real runs come in phase 3.
