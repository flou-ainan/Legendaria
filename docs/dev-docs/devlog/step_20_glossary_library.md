# Step 20 — Glossary library with an active glossary

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_03_review_glossary.md (§3.1b)

## Why

The owner asked to choose which glossary is in use (in Blender: a drop-down with New, Import and Export). Until now there was one global file, plus the project file and `--glossary`.

## What was done

- **`review/glossary.py`:**
  - the library at `<config dir>/glossaries/<name>.txt`;
  - `safe_name` (portable file names);
  - `list_names`, `active_name` (config `review.glossary`, default "default"), `create`, `import_file` (validates the content; `overwrite` flag), `export_file`, `delete`, `resolve` (a file path or a library name);
  - `migrate_legacy`: the old `glossary.txt` becomes "default";
  - `global_file()` now returns the active library glossary.
- **`config.update_user_config()`:** merges changes into the user's `config.json`, validated. This is how the active glossary is remembered.
- **Config:** `review.glossary` (default "default"), with schema.
- **CLI:**
  - `flosub glossary list | new NAME [--activate] | use NAME | import FILE [--name] [--overwrite] | export NAME --to FILE | delete NAME | show [NAME] | path [NAME] | add ENTRY [--name | --media | --file]`;
  - `add` writes to the active glossary by default;
  - `--glossary` on `transcribe` and `review` takes files or library names.
- Every operation is in the engine, so the Blender drop-down (stage 3c), the web GUI (plan 05) and other clients call the same commands (ADR-011).

## How it was tested

- `uv run pytest`: **90 passed** (new `test_glossary_library.py`: default and migration, new/use/add/list, import/export/delete with an overwrite guard, names and files in `--glossary`, invalid names). Ruff is clean.
- `flosub glossary list` on the dev machine: an empty library, with "default" active.

## Pending / next steps

- Stage 3c: the Blender UI (glossary drop-down with New/Import/Export/Edit, suggestions list, Add to glossary).
- Publish engine 0.1.0.dev4 when the owner approves.
