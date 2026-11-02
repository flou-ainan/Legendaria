# ADR 020 — Solar Linear icons for the toolbar

**Status:** accepted (owner's request)
**Date:** 2026-10-27
**Related:** plan 08

## Context

The toolbar used emoji and Unicode symbols (🧲 ⏯ ↶ ✂), which look different on every system and clash with each other. The owner asked for the Solar Linear set (480 Design, https://www.svgrepo.com/collection/solar-linear-icons/).

## Decision

- Use **Solar Linear** icons. The set is **CC BY 4.0**, so it needs attribution: the credit is in the README licence section, in `lib/icons.ts`, and here.
- Only the icons the editor uses are copied into `web/src/lib/icons.ts` (inner SVG paths, `stroke="currentColor"`, 24×24), rendered by `components/Icon.svelte`. No icon package is added to the bundle.
- To add one: take its path from the SVG Repo page and add a line to `icons.ts`.

## Alternatives considered

- **Install `@iconify-json/solar`:** thousands of icons at build time for twelve in use; copying the few is simpler and hackable.
- **Keep emoji:** inconsistent across platforms (Windows, macOS, Linux render them differently).

## Consequences

The toolbar icons follow the text colour and scale with the font size. The menu, the cue list and the zoom buttons still use text symbols; they can move to `Icon` one by one.
