# Step 19 — Plan 03 stage 3b: LLM reviewer with a guard

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Related plan:** planning/plan_03_review_glossary.md (§3.2–3.4, §7); ADR-010

## What was done

- **Owner request (recorded first):** a **glossary library** with an active glossary, and in Blender a drop-down with New, Import and Export. This is plan 03 §3.1b, scheduled before stage 3c.
- **`review/llm.py`:**
  - an OpenAI-compatible client (stdlib only): `/models`, `/chat/completions` in JSON mode with a fallback when the server rejects it;
  - tolerant JSON parsing;
  - Ollama `unload()` (`keep_alive: 0`);
  - provider presets in `defaults/providers.json` (ollama, lmstudio, llamacpp, openai, gemini, anthropic, openrouter), plus the user's `providers.json`;
  - keys read from the environment variable named in the config.
- **`review/reviewer.py`:**
  - batches with context lines; uncertain words marked `[[…]]`;
  - an editable prompt template `defaults/review_prompt.txt` (a user copy in the config dir wins);
  - the answer is `{"fixes": {"<n>": "line"}}`, with only the changed lines;
  - the answer is diffed word by word into suggestions;
  - **guard v2:** no deletions; similarity ≥ 0.5 unless the change is only accents, case or punctuation; the old words must be uncertain, or the new text a glossary term;
  - the count of rejected changes is reported.
- **CLI:**
  - `review --llm/--no-llm --provider --model --base-url`;
  - `transcribe --review` uses the configured profile;
  - `llm check|providers`;
  - glossary (layer 2) suggestions take priority over overlapping LLM ones.
- **Config:** `review.profile` (auto/light/standard/full) and `review.llm` (enabled auto, provider, base_url, model, api_key_env, batch_lines, context_lines, max_change_ratio, timeout_s, unload_after), with schema and validation. With `enabled: auto`, an unreachable server only produces a warning, and the glossary still applies.
- **Tests:** `test_llm_review.py`, with a fake OpenAI-compatible HTTP server: model pick, the guard (rewrite, deletion, invention, translation, accents), the fixes format, a skipped batch, auto-mode degradation, the CLI end to end, `llm check`. The CLI tests now pass `--no-llm`: one test had been calling the real local Ollama and took 57 s.

## Real tests (owner's crochet video, 88 segments, `llama3.1:8b` via Ollama)

1. Asking for all lines back: two batches were dropped (21/24 lines), and 5 suggestions deleted filler words. This led to the "only changed lines" format and the no-deletion rule.
2. With the new format: no dropped batches; "fake → falso" (a translation) and "o cenoura → a bolsa Beth" (an invention from the glossary) slipped through. This led to the similarity floor.
3. Final: **the 4 correct glossary suggestions only, 47 LLM rewrites rejected**, about 22 s.

Conclusion: on this video the glossary did all the useful work, and the LLM layer stays optional. Recorded in plan 03 §7.

## How it was tested

- `uv run pytest`: **85 passed in about 3 s** (no network). Ruff is clean.
- Real runs as above. The outputs are in `docs/local/teste-glossario-2026-10-26/llm/` (gitignored).

## Pending / next steps

- Glossary library (§3.1b), then stage 3c (Blender UI).
- Publish engine 0.1.0.dev4 when the owner approves.
- Compare other local or cloud models before recommending the LLM layer.
