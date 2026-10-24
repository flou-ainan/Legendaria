# ADR 005 — Language policy: English for development, translatable user content

**Status:** accepted
**Date:** 2026-10-24

## Context

The project should welcome contributors from anywhere and users who do not speak English, with Brazilian Portuguese as the first non-English audience.

## Decision

- **English:** code, identifiers, comments, commit messages, folder names, `PROJECT.md`, plans, devlogs, ADRs, and everything else in `docs/dev-docs/`.
- **Translatable user content, with English as the source and `pt_BR` always kept up to date:**
  - The README: `README.md` plus `README.pt-BR.md`, each linking to the other at the top.
  - User docs, organized by language: `docs/user/<lang>/`.
  - The Blender UI: strings written in English and translated through `bpy.app.translations`, with the dictionaries in `blender_addon/legendaria/locales/<lang>.json`. The add-on follows Blender's own language setting.
- **Engine CLI:** English only (a power-user tool). Anything the add-on shows to the user is translated by the add-on.
- Contributors add a language by adding files. No code changes are needed.

## Consequences

- Every new UI string needs an English source plus a `pt_BR` entry, checked in review. Later, a test can flag missing keys.
- Blender uses its own locale codes (for example `pt_BR`), and the locale file names follow them.
