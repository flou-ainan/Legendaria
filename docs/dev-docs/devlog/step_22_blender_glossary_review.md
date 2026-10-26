# Step 22 — Blender UI for the glossary and the review (plan 03, stage 3c)

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

The add-on now exposes the glossary library and the review. All logic stays in the engine (ADR-011): the add-on only runs `flosub glossary …` and `flosub review …` and shows the results.

- **Glossary box in the panel:**
  - a "Use glossary" checkbox; when it is off, Generate passes `--no-glossary` and Review passes `--no-glossary` too;
  - a drop-down with the library (`glossary list`). Choosing an entry runs `glossary use NAME`. "default" and the active glossary are always listed, even before their file exists. Each entry's tooltip shows its term and fix counts;
  - buttons for New (`glossary new NAME --activate`), Import (`glossary import FILE`, then `use`), Export (`glossary export NAME --to FILE`) and Edit (creates the file if needed, then opens it with the system editor);
  - "Add to glossary": a dialog prefilled with the selected caption's text, trimmed of punctuation. The user keeps only the word and picks the target, either the active glossary or the video's folder (`legendaria-glossary.txt`, through `--media`). A `wrong -> right` entry is kept as typed. The report says where the term was saved and that it applies from the next run. Nothing is added automatically (owner decision, plan 03 §5.4).
- **Review:**
  - "Review captions" runs `flosub review <transcript> --mode suggest --no-llm|--llm` in the background (modal timer, progress, cancel) and loads the pending suggestions of `<name>.review.json` into a list;
  - each row has a checkbox, `before → after` (an icon tells glossary from AI suggestions), and a `+` button that opens "Add to glossary" with the corrected text;
  - the selected row shows its reason;
  - All / None buttons;
  - "Use AI (experimental)" adds `--llm`, and the panel then shows a warning that it is experimental.
- **Apply corrections:**
  - runs `flosub review apply … --ids … --reject-rest --format cues --style <style>`, which corrects the transcript, re-times the words and re-exports the cues;
  - then rebuilds only the captions that touch a corrected word. For each suggestion, the span grows to cover every old caption and every new cue it overlaps, so the midpoint rule of `create_strips` replaces exactly those captions. Every other caption, including the user's hand edits, is untouched. A hand edit inside one of the rebuilt captions is lost (plan 03, open question 2).
- **Properties:**
  - `MIN_ENGINE` and the installer's `ENGINE_SPEC` move to 0.1.0.dev4;
  - new `LegendariaSuggestion` items and the settings `glossary`, `use_glossary`, `use_ai_review`, `suggestions`, `suggestion_index` and `review_path`.
- **`engine_bridge.run_events`:** runs a quick command with JSON-lines events and raises on an `error` event.
- New module `review_ops.py`. pt_BR translations for every new string. Counts are written as "Suggestions found: {count}." so that the Portuguese text reads well for 1.

## Known limitations

- The reason shown for a suggestion ("glossary fix", "LLM: …") comes from the engine in English.
- Engine 0.1.0.dev4 is not on PyPI yet. Until the owner approves the tag, "Install engine" in a fresh Blender cannot install a version this add-on accepts. A development install (`uv tool install ./engine`) works.

## Files

- `blender_addon/legendaria/review_ops.py` (new), `properties.py`, `panel.py`, `operators.py` (`--no-glossary`), `engine_bridge.py` (`run_events`), `installer.py` (spec), `__init__.py` (module list), `locales/pt_BR.json`.
- `blender_addon/tests/blender_smoke.py`: a throwaway `LEGENDARIA_CONFIG_DIR`; checks for the glossary library and suggestions; with `--real`, a review with a `word -> Zebrafix` fix and apply.
- `blender_addon/tests/ui_walkthrough.py`: a review step and the `5-review` screenshot, with a throwaway config folder.
- Docs: `PROJECT.md` (add-on file map regenerated, current state), plan 03 (done; DoD), `CHANGELOG.md`.

## How it was tested

- Add-on pytest: 35 passed. Ruff is clean. The i18n test passes, with nothing missing or unused.
- `blender_smoke.py` on Blender 4.2.23 and 5.2.3 passed every check, both with fixture cues (28 checks) and with `--real` (42 checks) on a 20 s Portuguese clip with the `small` model. In the real run:
  - the review found the fix, and Apply put "Zebrafix muito bem-vindos" on screen;
  - exactly one caption was rebuilt;
  - range regeneration and re-styling still pass.
- The first fixture run caught a bug: in a fresh config, creating a glossary removed "default" from the drop-down, so switching back failed. "default" is now always listed.
- `ui_walkthrough.py` under Xvfb on 5.2.3 ran in en_US and pt_BR. The screenshot shows the glossary row, the review list with `Olá → Zebrafix`, All/None and Apply. When Blender is started without a file, the splash covers the panel; pass an empty `.blend` to avoid it.
