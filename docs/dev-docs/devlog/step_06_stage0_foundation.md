# Step 06 — Stage 0: community files, CI, repository settings

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md (section 7, stage 0)
**Related decision:** ADR-008

## What was done

- **Community files:**
  - `CONTRIBUTING.md`: setup, branch/commit/PR workflow, docs rules, code style, adding a language, licensing.
  - `CODE_OF_CONDUCT.md`: Contributor Covenant 2.0, the text provided by GitHub's API. Reports go to the maintainer's email (owner's choice).
  - `SECURITY.md` (private reporting) and `CHANGELOG.md` (Keep a Changelog).
  - Both READMEs link to `CONTRIBUTING.md`.
- **Quality tooling:**
  - `ruff.toml` (py310 target, rules E/F/W/I/UP/B/SIM/RUF).
  - `.pre-commit-config.yaml` with ruff v0.16.10 and pre-commit-hooks v6.0.0.
  - `.editorconfig`, and `.gitattributes` with LF line endings for Windows checkouts.
  - The two brand generator scripts were reformatted by ruff, and an en dash in a comment was replaced; their behavior did not change.
- **CI** (`.github/workflows/ci.yml`):
  - Runs pre-commit on Ubuntu, macOS and Windows.
  - Runs the engine tests once `engine/pyproject.toml` exists.
  - A single aggregate job, `ci`, is the required status check.
  - Actions are pinned to releases at least two weeks old (checkout v7.0.1, setup-uv v10.2.0) and pre-commit to 4.6.2.
- **Templates:** issue forms (bug, feature, translation), blank issues disabled, contact links to Discussions and to private security reports; a PR template with the docs checklist.
- **GitHub settings:**
  - Discussions enabled, wiki disabled (docs live in the repo).
  - Private vulnerability reporting enabled.
  - Topics added.
  - New labels: `translation`, `triage`, `engine`, `blender-addon`, `installer`, `platform: windows|macos|linux`.
- **Development machine:** installed `uv` 0.13.5 in `~/.local/bin` (user install).

## Files touched

- New: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `ruff.toml`, `.pre-commit-config.yaml`, `.editorconfig`, `.gitattributes`, `.github/**`
- Changed: `README.md`, `README.pt-BR.md`, `docs/PROJECT.md`, plan 01, ADR-008, `assets/brand/source/*.py` (formatting only), this file

## How it was tested

- `uvx pre-commit@4.6.2 run --all-files`: all hooks pass.
- CI runs on this PR.

## Pending / next steps

- After the first green CI run: add `ci` as a required status check on `main`.
- Reserve the `legendaria` name on PyPI (needs the owner's PyPI account).
- Stage 1: the engine.
