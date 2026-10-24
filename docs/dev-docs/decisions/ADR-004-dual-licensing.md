# ADR 004 — Engine under MIT, Blender add-on under GPL-3.0-or-later

**Status:** accepted
**Date:** 2026-10-24

## Context

The repository started under MIT. Blender's official extensions platform requires GPL-3.0-or-later, and code that uses Blender's Python API is generally treated as GPL-bound.

## Decision

- `engine/` and the rest of the repository: **MIT** (the root `LICENSE`, plus `engine/LICENSE`).
- `blender_addon/`: **GPL-3.0-or-later** (`blender_addon/legendaria/LICENSE`, plus SPDX headers in each file).
- The README explains the split.

## Alternatives considered

- **All GPL:** simpler, but it would stop the engine from being reused in projects that are not GPL.
- **All MIT:** incompatible with the Blender extensions platform.

## Consequences

- The add-on talks to the engine only through a process boundary and files (ADR-003), so the two licenses do not mix.
- Contributors must keep code from crossing between the two folders.
