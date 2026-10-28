# ADR 013 — Blender 5.2 LTS is the minimum supported version

**Status:** suspended by ADR-014 (the add-on is frozen; not implemented).
**Date:** 2026-10-26
**Supersedes:** the "Blender 4.2+" support decided in plan 01/02.

## Context

The add-on supported Blender 4.2 LTS and newer. Doing so cost us:
- `compat.py` shims (`sequences` → `strips`, `frame_end` → `length`, the alignment API changes);
- a second CI job;
- behaviors that differ between versions. For example, the `transform.origin` of a text strip is measured differently in 5.2 (plan 04 §11.2), and 4.2 places a new sound strip one frame later.

Blender 5.2 is an LTS release. Legendária is a new project with no installed base to keep working.

## Decision

- The add-on targets **Blender 5.2 LTS and newer** (`blender_version_min = "5.2.0"`).
- Only 5.x APIs are used. The compat shims for 4.x are removed.
- CI runs the Blender smoke test on 5.2 only, and later also on newer releases.

## Alternatives considered

- **Keep 4.2+:** more potential users on older LTS releases, at the cost of version-specific code and behavior for a project that has no 4.x users yet.

## Consequences

- People still on Blender 4.x must update Blender to use the add-on. The README must say so clearly.
- Native animations can use 5.x behavior directly (plan 04 §11.4).
- Implementation, after the owner's manual test:
  - the manifest;
  - `compat.py` simplified or removed;
  - the CI matrix;
  - the docs that say "4.2+" (README, CONTRIBUTING, `PROJECT.md`, plans).
