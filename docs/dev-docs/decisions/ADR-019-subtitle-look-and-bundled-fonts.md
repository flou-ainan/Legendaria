# ADR 019 — Subtitle look overrides in the project, and bundled fonts

**Status:** accepted (agent proposal, applied after the owner asked for a quick position/size menu and more fonts)
**Date:** 2026-10-27
**Related:** ADR-012 (`.ass` + libass), ADR-016 (project file), plan 08

## Context

The owner wants a quick menu to move and scale all the subtitles (sliders, plus Top and Bottom presets) and more font choices. Until now the look came only from the style in the config, and the font was whatever fontconfig found on the machine, so the preview and the export could differ between computers.

## Decision

- **`look` in the project file** (optional, no version bump, absent means "the style as is"): `{ "font": family, "size": multiplier 0.3–3, "y": 0–1, "color": "#rrggbb", "outline_color": "#rrggbb", "box": bool, "uppercase": bool }` (the last four were added in step 42; colours keep the style's alpha, `box` is the rectangle behind the text, `uppercase` overrides the style, so the pop's caps can be turned off). `y` is the text centre's height above the bottom edge as a fraction of the video height. It overrides the style's position; `size` multiplies font size, outline and shadow; `font` replaces the style's font. The server validates and clamps it (`project.clean_look`), and `ass.with_look` applies it. The preview `.ass`, the `.ass` export and the burned MP4 all go through the same function, so they agree.
- **In the editor** the override is project state: undoable (grouped while a slider moves), autosaved, kept in the recovery copy.
- **Bundled fonts:** 19 families under the SIL Open Font License (Montserrat, Lato, Raleway, Nunito, Comfortaa, Fredoka One, Oswald, Anton, Bebas Neue, Passion One, Archivo Black, Titan One, Righteous, Bangers, Orbitron, Press Start 2P, Playfair Display, Merriweather, Pacifico), picked from the owner's font folder for variety (sans, rounded, condensed, heavy, display, comic, tech, pixel, serif, script). About 1.5 MB in `engine/legendaria_engine/fonts/`, catalogued in `fonts.json`. The server serves them (`/api/fonts/<file>`, only names in the catalogue), the preview loads them all up front, and the export copies them next to the subtitles and gives FFmpeg `ass=…:fontsdir=fonts`, so nothing has to be installed.
- **Adding a font:** drop the `.ttf` in the folder and add a line to `fonts.json`.

## Alternatives considered

- **Per-cue overrides:** the owner's study wants "apply to all" versus "just this one" later; `look` is the project-wide level, and a per-cue `look` can be added on the same shape.
- **Using any installed font:** unreliable across machines and impossible in the browser preview without uploading the file; kept only for the style's own default font (via fontconfig).
- **A heavier font set (the owner's folder has about 1,250 files):** a long list is hard to choose from and bloats the wheel; the catalogue makes it easy to grow.

## Consequences

- The wheel grows by about 1.5 MB.
- A `look.font` that is not in the catalogue still works on the machine that has it, but the preview falls back to JASSUB's font.
- Where a family has only a regular cut (Anton, Bebas Neue), a style with `bold: true` gets libass's synthetic bold, in the preview and in the export alike.
