# Step 18 — Plan 03 stage 3a: glossary, Whisper hotwords, deterministic fixes, suggestions

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_03_review_glossary.md (§3.1–3.4, §3.6); ADR-010

The session was interrupted by the owner's PC freeze (KI-001); the uncommitted files survived and work resumed here.

## What was done

- **`legendaria_engine/review/`:**
  - `glossary.py`:
    - plain-text glossary: terms and `wrong -> right` / `→` fixes, `#` comments;
    - `fold()` (case-, accent- and edge-punctuation-insensitive);
    - merge order: global, then project (`legendaria-glossary.txt` next to the media or transcript), then `--glossary`;
    - `add_entry()` creates the file with a header, ignores duplicates and keeps comments.
  - `bias.py`: terms → Whisper `hotwords` within a 600-character budget (layer 1).
  - `fix_rules.py` (layer 2):
    - explicit fixes over spans of 1–4 words;
    - fuzzy matches (difflib on folded text, threshold 0.82, stricter for short terms) for words with confidence below 0.5;
    - keeps trailing punctuation and a capital first letter.
  - `align.py`: replaced words get the old span's time, split by length, confidence 1.0.
  - `suggestions.py`: review document v1 (`<name>.review.json`), `apply()`.
- **Engine wiring:**
  - `Options.hotwords` → faster-whisper `hotwords`;
  - config `review` (mode suggest/auto, glossary_bias, thresholds) with schema and validation.
- **CLI:**
  - `transcribe --glossary FILE (repeatable) --no-glossary --review`;
  - `review FILE.json [--mode]`;
  - `review apply FILE.review.json --ids|--all [--reject-rest] [--format --style]`;
  - `glossary path|show|add [--media|--file]`, the base for "Add to glossary" (plan 03 §3.6);
  - new event `suggestion`.
- Engine version **0.1.0.dev4** (not yet published).

## How it was tested

- `uv run pytest`: **76 passed** (new: `test_glossary.py`, `test_fix_rules.py`, and the CLI glossary/review flow). Ruff is clean.
- **Real, on the owner's crochet video**, with a 4-line glossary (`Mariana Enacles`, `bolsa Beth`, `Poliéster`, `crochê`) and no fix lines:
  - **Layer 2** on the old transcript: 4 suggestions, Mariana Nakley → Mariana Enacles, polieste → Poliéster (×2), Bolsa Bet → Bolsa Beth. The capital letter was kept after a first run lowercased "Bolsa"; that fix is covered by a test.
  - **Layer 1**, transcribing 0–75 s with `small` on the GPU: without the glossary "Bet / Nakley / polieste", with it **"Beth / Enacles / poliéster"**.
- The outputs are in `docs/local/teste-glossario-2026-10-26/` (gitignored).

## Pending / next steps

- Publish engine 0.1.0.dev4 (tag), with the owner's approval.
- Stage 3b: the LLM reviewer. Stage 3c: the Blender UI (glossary, suggestions, "Add to glossary").
