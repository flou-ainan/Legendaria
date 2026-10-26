# ADR 010 — Caption accuracy: glossary in three layers, LLM reviewer as suggestions

**Status:** accepted
**Date:** 2026-10-25

## Context

Real use showed Whisper getting names and domain terms wrong ("polieste", "Nakley", "Bet") with low confidence. The owner wants a reviewer with a user-supplied dictionary. The engine must also run on weak devices (CPU-only, mobile later) where an LLM is not possible.

## Decision

- The glossary is a plain text file (terms plus optional `wrong -> right` lines), global and/or per project.
- Three independent, optional layers:
  1. **Transcription bias:** glossary terms go into faster-whisper's `hotwords` / `initial_prompt`. Free; works everywhere.
  2. **Deterministic fixes:** explicit pairs, plus fuzzy matching of low-confidence words to glossary terms. No AI.
  3. **LLM reviewer:** any **OpenAI-compatible** chat server, local first (Ollama, LM Studio, llama.cpp, vLLM). Cloud providers are optional, with the user's key read from an environment variable and never stored in project files.
- Output is a **review document** with suggestions (before → after, source, reason). Mode `suggest` is the default and `auto` is available. Both are configurable.
- A **guard** rejects LLM rewrites that change too much: line count, edit distance, words outside the uncertain or glossary areas.
- Word timings are re-aligned after a correction.
- **Device profiles** (light / standard / full) select the layers automatically; without an LLM the pipeline degrades to layers 1 and 2.

## Alternatives considered

- **LLM only:** slow (about 3 s per line on an 8 GB GPU), unavailable on weak devices, and it can rewrite speech ("perfeito → perfeita" in the prototype).
- **Ollama native API only:** simpler, but it locks users to one tool. The OpenAI-compatible API covers Ollama and the others.
- **Vendor SDKs:** extra dependencies for every provider. A small stdlib HTTP client is enough for chat completions.
- **Applying corrections automatically by default:** risks changing what the speaker said.

## Consequences

- New engine package `legendaria_engine/review/` and new CLI commands (`review`, `review apply`, `glossary`, `llm check`).
- The UI needs a suggestions list (Blender UIList; later the web GUI).
- Evidence and details: plan 03.
