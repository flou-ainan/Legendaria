# Step 35 — Look menu, bundled fonts, translation files, mobile toolbar

**Date:** 2026-10-27
**Agent/author:** Claude Code (Sonnet 5.5), with flou-ainan
**Related:** ADR-019, plan 08 (priority round 3)

## What was done

- **Look menu** (`LookMenu.svelte`, "Look" button in the tool row): Top and Bottom presets, height and size sliders, a font drop-down and Reset. Stored as the project's `look` (ADR-019), so it is undoable, autosaved and identical in the preview, `.ass` and burned MP4.
- **Bundled fonts:** 19 SIL OFL families from the owner's `~/.local/share/fonts` (1.5 MB), `fonts/fonts.json` catalogue, `/api/fonts/<file>`, `fonts.py`, and FFmpeg gets `fontsdir` through the staged folder. The preview loads all of them up front.
- **Translations are plain files:** one JSON per language in `web/src/locales/`, found by `import.meta.glob`, with the language's own name in `_name`, English fallback for missing keys, `locales/README.md` for translators, and a Vitest check (unknown keys, placeholders, pt-BR complete). Adding a language needs no code.
- **Mobile toolbar:** under 900 px the tool row is one line that slides sideways, with smaller buttons and tighter spacing.
- Plan 08 now lists these as priority round 3, before the UX-study items.

## Files touched

- Engine: new `fonts.py`, `fonts/` (19 TTF + `fonts.json` + `README.md`); `ass.py` (`with_look`), `project.py` (`look`, `clean_look`), `media.py` (staged fonts), `server.py` (state `fonts` and `base`, `/api/fonts/`, look in the preview and exports), `schemas/project.schema.json`, tests.
- Web: new `LookMenu.svelte`, `locales/README.md`, `lib/locales.test.ts`; changed `Toolbar.svelte`, `Player.svelte`, `App.svelte`, `lib/api.ts`, `lib/editor.svelte.ts`, `lib/i18n.ts`, both locales, `e2e/smoke.mjs`.
- Docs: ADR-019, plan 08, `PROJECT.md`, `chat-context.md`.

## How it was tested

pytest 130 passed (look round trip and clamping, `with_look`, bundled font served, preview `.ass` with the look, the real cut + burn with `fontsdir`); Vitest 11 passed; svelte-check clean; the browser test picks Top and Anton and checks the project and the preview `.ass`; screenshot of the narrow toolbar and the menu.
Not covered: the burned video's frame with a bundled font compared with the preview (pixel diff), touch use of the sliders on a real phone.

## Pending

Plan 08 step 1 (contextual toolbar), then the orange track, the generate-captions sheet and per-cue style.
