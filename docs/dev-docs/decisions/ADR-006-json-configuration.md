# ADR 006 — Hackable behavior through layered JSON config files

**Status:** accepted
**Date:** 2026-10-24

## Context

Users and contributors should be able to change defaults, add models, tune subtitle splitting, and create style presets without editing code.

## Decision

- Behavior lives in JSON:
  - Engine: `config.json` (defaults) and `models.json` (model catalog).
  - Add-on: `presets/*.json` (strip styles) and `locales/*.json` (translations).
- **Layering:** shipped defaults → user file in the per-OS config dir (resolved with `platformdirs`) → CLI flags or UI values. Users never edit the installed files.
- Each file carries a `"version"` field and has a published **JSON Schema** (`engine/schemas/`), so editors validate and autocomplete it.
- `opensub config show` prints the merged config and `opensub config path` prints where the user file lives.

## Alternatives considered

- **TOML/YAML:** nicer to write by hand, but JSON needs no extra parser in Blender's Python, has the widest tool support, and was requested explicitly.

## Consequences

- JSON has no comments, so documentation goes into the schemas (`description` fields) and into the user docs.
- Config loading must validate its input and give clear errors that point to the bad key.
