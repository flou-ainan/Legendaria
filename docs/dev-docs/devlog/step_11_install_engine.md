# Step 11 — Stage 2b: "Install engine" button (and engine 0.1.0.dev1)

**Date:** 2026-10-24 (overnight, autonomous)
**Agent/author:** Claude Code (Opus 5.5)
**Related plan:** planning/plan_02_blender_addon.md (§6, 2b); plan 01 decision 9

## What was done

- **Engine 0.1.0.dev1 released to PyPI** (PR #9, tag `v0.1.0.dev1`, Trusted Publishing). It has the cue styles the add-on needs. CHANGELOG reorganized by release. Verified with `uvx --from legendaria==0.1.0.dev1 flosub --version`.
  - The GitHub "release page" for the tag was **not** created: the auto-mode safety check blocked publishing a new public page overnight. The owner can create it in the morning (optional).
- **`blender_addon/legendaria/installer.py`** (no bpy):
  1. Downloads **uv 0.13.0** (pinned, released ≥ 2 weeks earlier) for the OS and CPU (Linux/macOS/Windows × x86_64/arm64) and checks its SHA-256 against the release's `.sha256` file.
  2. Runs `uv venv --python 3.11`.
  3. Runs `uv pip install "legendaria[cuda]>=0.1.0.dev1,<0.2"`, with `[cuda]` only when an NVIDIA GPU is detected (`nvidia-smi -L`) or forced with `LEGENDARIA_INSTALL_CUDA=0|1`.
  4. Runs `flosub models download small`, with progress parsed from the JSON events.
  - Everything goes into `<data dir>/legendaria/engine/` (`uv/`, `python/`, `venv/`; caches too, via `UV_PYTHON_INSTALL_DIR` and `UV_CACHE_DIR`). The uv cache is deleted after the install, because the venv is self-contained. Uninstall = delete the folder.
  - It runs on a thread with a readable `state` (step, message key, params, progress, error), and supports cancel.
- **UI:**
  - `install_engine` (confirmation with the download size and the folder, then a modal timer).
  - `cancel_install`, and `uninstall_engine` (with confirmation).
  - `panel.draw_engine_box()`, shared with the preferences: shows "not found" with Install, the progress bar "Step n of 4: …" with Cancel, the failure message, and "engine older than this add-on needs" with Update.
  - `MIN_ENGINE = "0.1.0.dev1"`, compared with a small version parser (`engine_bridge.version_key`).
- **i18n:**
  - Installer messages are marked with `N_()` (translated when shown).
  - The i18n test also scans `N_` and now **fails on unused translations**. That surfaced "Engine not found", which was shown untranslated; it is fixed through `i18n.N_` and `tr()` when displayed.
- **Tests:**
  - `test_installer.py`: uv asset names for 6 OS/CPU pairs, checksum, tar and zip extraction, GPU override, one-folder layout, version ordering.
  - `test_source_rules.py`: a static check of the confirm-dialog icons (see bug 1).
- `ui_walkthrough.py --install confirm|run` scripts the install flow; on an error it now quits instead of hanging.

## Bugs found and fixed

1. **The "Install engine" button would have failed on click**: `invoke_confirm(icon=...)` accepts only NONE / WARNING / QUESTION / ERROR / INFO, and the code used `IMPORT` / `TRASH`. Only the GUI walkthrough found it; it is now also a static test.
2. **Size estimate ignored the CUDA override**: the dialog and the installer now share `installer.wants_cuda()`.
3. **Disk use with GPU support was 3.6 GB**, because the uv cache kept a second copy of the packages. Deleting the cache after install is safe; real totals are about 0.8 GB (CPU) or 2.9 GB (GPU) plus the model. The dialog says ~1.3 GB / ~3.5 GB including `small`.
4. **"Engine not found" was never translated** (see i18n above).

## How it was tested

- `uvx pytest blender_addon/tests`: 35 passed. Engine tests: 51 passed. Ruff is clean.
- **Real installer runs from scratch** in isolated `XDG_DATA_HOME` / `XDG_CONFIG_HOME` with a minimal PATH:
  - CPU: about 36 s; `flosub 0.1.0.dev1` from PyPI works after the cache cleanup; the add-on's `find_engine()` picks the managed engine.
  - GPU (`[cuda]`): about 158 s; the managed engine **transcribed on CUDA (float16)**, which proves the CUDA-lib re-exec works inside the managed venv.
- **GUI** (xvfb, installed extension, isolated HOME/data):
  - "not found" panel → confirmation dialog ("cerca de 1,3 GB") in pt_BR (4.2.23) and en_US (5.2.3);
  - a real install from the UI on 5.2.3: progress "Etapa 1 de 4: Baixando o uv…", Cancel shown, engine detected at the managed path when finished.
- All test installs were deleted afterwards. **Note: the dev machine's root disk has only about 9.8 GB free.**

## Pending / next steps

- Stage 2c: regenerate a time range.
- The owner tries Install / Uninstall on a machine or user account without the dev tools.
