# Step 02 — English dev docs, bilingual README, product scope in plan 01

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md

## What was done

- **Language policy applied (ADR-005):** all dev docs translated to English, and folders and files renamed:
  - `PROJETO.md` → `PROJECT.md`
  - `planejamento/` → `planning/`, `decisoes/` → `decisions/`
  - `passo_NN_*` → `step_NN_*`, `plano_NN_*` → `plan_NN_*`
  - New `references/` folder.
- **README:** `README.md` (English) and `README.pt-BR.md`, each linking to the other.
- **Origin brainstorm:**
  - The real conversation is now local only (`docs/whisper-blender-brainstorm.md` is in `.gitignore`), because it holds private data.
  - A generic, sanitized version was written in `references/origin_brainstorm.md`.
- **Plan 01 expanded:**
  - Product vision and principles, roadmap phases 1–5.
  - Decisions on the earlier open questions: venv, `small` model plus in-app download, licenses, Blender 4.2+.
  - i18n, JSON config, cross-platform constraints.
  - A new list of open questions.
- **New ADRs:** 004 (MIT engine / GPL add-on), 005 (language policy), 006 (layered JSON config), 007 (cross-platform). ADR-003 is now accepted.
- `AGENTS.md` now covers the language policy and the engineering principles.

## Why

Direction from the project owner: easy access for users and contributors, bilingual (en + pt-BR, open to more), cross-platform, hackable through JSON, an easy installer and a GitHub Pages site later on.

## Files touched

- `AGENTS.md`, `README.md`, `README.pt-BR.md`, `.gitignore`
- `docs/PROJECT.md` (renamed and rewritten), `docs/dev-docs/README.md`
- `docs/dev-docs/planning/plan_01_mvp_engine_blender.md`
- `docs/dev-docs/decisions/ADR-001..007`
- `docs/dev-docs/devlog/step_00..02`
- `docs/dev-docs/references/origin_brainstorm.md`

## How it was tested

Documentation only. Checked that `git status` does not list the private brainstorm.

## Pending / next steps

- The owner answers the open questions in plan 01, section 7.
- Then: stage 1 (engine).
