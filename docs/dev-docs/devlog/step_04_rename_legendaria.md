# Step 04 — Rename to Legendária (`flosub` CLI) and protect `main`

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_01_mvp_engine_blender.md (decisions 16–18)

## What was done

- **Naming research, round 2:** SubFlow, VoxCut, vocut, subx, flosub, legio, cuex and lgd. Results are in ADR-009.
- **Decision:** the product is **Legendária**, the identifiers are `legendaria`, and the CLI is **`flosub`**. New ADR-009.
- **GitHub:**
  - Repository renamed `Open-Subtitler` → `Legendaria`; the old URL redirects. Local `origin` remote updated, and the repo description updated.
  - `main` protected: PR required (0 approvals, so the owner can merge alone), enforced for admins, linear history, no force-push or deletion, conversation resolution required.
  - Merge settings: squash only, PR title and body used as the commit message, head branches deleted after merge.
- **Docs:**
  - Every `opensub` / `open_subtitler` / `open-subtitler` identifier in the README, `PROJECT.md`, plan 01 and the ADRs replaced with `flosub` / `legendaria` / `legendaria_engine`.
  - READMEs now open with the name, the slogan and the CLI name.
  - Plan 01: decisions 16–18; translation moved to the backlog; no open questions left; stage 0 checklist updated.
- This is the first change made through a branch and PR (`docs/rename-legendaria`).

## Files touched

- `README.md`, `README.pt-BR.md`, `docs/PROJECT.md`
- `docs/dev-docs/planning/plan_01_mvp_engine_blender.md`
- `docs/dev-docs/decisions/ADR-003`, `ADR-004`, `ADR-005`, `ADR-006` (identifiers), `ADR-009` (new)
- this file

## How it was tested

- `git grep` finds no old identifiers outside the devlog.
- `gh api .../branches/main/protection` returns the expected settings.

## Pending / next steps

- Logo.
- The rest of stage 0: community files, `ruff` / `pre-commit`, CI (then make it a required check), labels, Discussions.
- Reserve `legendaria` on PyPI.
