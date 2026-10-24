# ADR 008 — Contribution workflow: the lightweight open-source standard

**Status:** accepted
**Date:** 2026-10-24

## Context

The owner has no prior experience running an open-source project and wants the way that serious but simple projects work: welcoming to first-time contributors, without bureaucracy.

## Decision

Adopt the conventions most mid-sized GitHub projects share:

- **Branches and PRs:** `main` is always releasable and protected (PR required, CI must pass). Work happens on short branches (`feat/...`, `fix/...`, `docs/...`), and each PR is squash-merged. The owner follows the same flow, so `main` history stays one commit per change.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). They make the history readable and the changelog easy to write.
- **Versions:** [SemVer](https://semver.org/), starting at `0.1.0`. A git tag `vX.Y.Z` plus a GitHub Release with notes marks each release. `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/).
- **Quality gates:** `ruff` (lint + format) and `pytest`, run locally through `pre-commit` and in GitHub Actions CI on Linux, macOS and Windows.
- **Community files:** `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.0, the version GitHub provides), `SECURITY.md`, issue templates (bug, feature, translation), and a PR template with a checklist (tests, devlog, `PROJECT.md`).
- **Triage:** labels `good first issue`, `help wanted` (for example the Apple Silicon backend) and `translation`. GitHub Discussions holds questions, so issues stay actionable.
- **The project's own docs rules** (AGENTS.md: plans, devlog, ADRs, `PROJECT.md`) apply to every PR.

## Alternatives considered

- **Pushing straight to `main`:** simpler for a single person, but it gives contributors no model to follow and lets CI breakage slip in.
- **Git-flow (`develop` + release branches):** too heavy for a small project.
- **A CLA or DCO sign-off:** not needed for now. The licenses (MIT/GPL) already cover inbound contributions ("inbound = outbound").

## Consequences

- Even small changes go through a PR. That costs a little, but every change gets a CI check and a record.
- Agents working on the repository must branch, commit with Conventional Commits, and open a PR instead of pushing to `main`, once stage 0 has enabled branch protection.
