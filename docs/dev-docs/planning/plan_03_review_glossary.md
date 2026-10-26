# Plan 03 — Accuracy: glossary and caption reviewer

**Status:** approved in principle (owner, 2026-10-25); details below to be confirmed per stage
**Date:** 2026-10-25
**Related decisions:** ADR-010 (review pipeline), ADR-011 (modular architecture: core / access / clients)
**Comes before:** plan 04 (CapCut-style animations, formerly "plan 03"), plan 05 (local API + web GUI)

## 1. Why

The owner used `flosub` on a real video (a crochet class, Portuguese, `small` model, GPU) and loaded the SRT into Kdenlive. The transcription was good overall, but it got names and domain terms wrong:

| Heard | Should be | Whisper confidence |
|---|---|---|
| polieste | Poliéster | 0.44 |
| Mariana Nakley | Mariana Enacles | 0.22 |
| bolsa Bet | bolsa Beth | 0.39 |

58 of the words in the 6-minute video had confidence < 0.5. Those are exactly the places a reviewer should look first.

### Evidence gathered (2026-10-25, owner's machine)

- **Glossary passed to Whisper** (faster-whisper `hotwords` or `initial_prompt`, with "Poliéster, Mariana Enacles, bolsa Beth, crochê") on the first 75 s: "Bet"→"Beth" and "Nakley"→"Enacles" were fixed **during transcription**, at no extra cost and with no LLM. ("Poliéster" still has to be confirmed; the check missed the accented form.)
- **LLM review through Ollama's OpenAI-compatible API** (`http://127.0.0.1:11434/v1`), with 14 lines, the same glossary and a strict prompt asking for JSON with the same number of lines:
  - `llama3.1:8b` (46 s) and `qwen2.5-coder:7b` (40 s) both fixed Enacles, poliéster and Beth.
  - `llama3.1:8b` also changed "perfeito"→"perfeita": grammatically defensible, but it **changes what the speaker said**. Hence suggestions that the user accepts, a guard against rewrites, and an "auto" mode only as an option.
  - It is slow (about 3 s per line on an 8 GB GPU, including model load), so it must run in the background with progress, and in batches.

## 2. Goals

1. Users can give the tool a **glossary** (names, brands, technical terms, and optionally "wrong → right" pairs) for one project or for every project.
2. The glossary improves the result at **three layers**, each optional (ADR-010):
   - **L1, transcription bias:** glossary terms become Whisper `hotwords` / `initial_prompt`. Free, works on CPU and later on mobile.
   - **L2, deterministic correction:** explicit "wrong → right" pairs, plus fuzzy matching (accent- and case-insensitive) of low-confidence words against the glossary terms. No AI.
   - **L3, LLM reviewer:** any **OpenAI-compatible** server (Ollama, LM Studio, llama.cpp server, vLLM…) by default; **cloud** providers optional, with the user's own key. The reviewer gets the lines, the glossary and the low-confidence words, and returns corrections.
3. Corrections are **suggestions** (before → after, source, reason) that the user accepts or rejects one by one or all at once. An **auto** mode applies them directly. Both are configurable.
4. **Device profiles**, because the engine will also run on weak devices (CPU-only PCs, mobile later):
   - `light`: Whisper on CPU (tiny/base/small) + L1 + L2.
   - `standard`: Whisper on GPU + L1 + L2.
   - `full`: standard + L3 (LLM).

   The profile is chosen automatically (a GPU and a reachable LLM server) and can be overridden in config. Everything degrades gracefully: no LLM means L1 + L2 still apply.
5. Word timings survive the corrections: corrected words are **re-aligned** to the time spans of the words they replace, so captions, CapCut animations (plan 04) and range regeneration keep working.
6. All of this is available from the CLI, from Blender, and later from the web GUI (plan 05), sharing the same engine code (ADR-011).

## 3. Design

### 3.1 Glossary files

- Plain UTF-8 text, easy to edit by hand:

  ```text
  # Names
  Mariana Enacles
  bolsa Beth
  # Terms
  Poliéster
  crochê
  # Explicit fixes (wrong -> right)
  polieste -> Poliéster
  Nakley -> Enacles
  ```

- **Global glossary:** `<config dir>/glossary.txt` (`flosub glossary path`).
- **Project glossary:** `legendaria-glossary.txt` next to the media, or any file passed with `--glossary FILE` (repeatable). Files are merged, project over global.
- `flosub glossary show|path|add "Term"` for quick edits. The Blender UI and the GUI read and write the same files.

### 3.1b Glossary library and the active glossary (owner, 2026-10-26)

Today the glossary is the sum of three sources (global file, project file next to the media, `--glossary` files). The owner wants to **choose which glossary is in use**:

- **A library of named glossaries:** `<config dir>/glossaries/<name>.txt` (for example "Crochê", "Canal Mariana", "Inglês técnico"). The config key `review.glossary` names the **active** one; the project file next to the media still adds to it.
- **Engine first (ADR-011):** `flosub glossary list | new NAME | use NAME | import FILE [--name] | export NAME FILE | delete NAME`. `add` writes to the active glossary by default. The HTTP API (plan 05) exposes the same operations.
- **Blender (stage 3c):** a **drop-down** with the library, plus **New**, **Import…**, **Export…** and **Edit** (opens the file), next to "Add to glossary" (§3.6).
- Migration: an existing `glossary.txt` becomes the glossary named "default".

### 3.2 Engine modules (`legendaria_engine/review/`)

| Module | Role |
|---|---|
| `glossary.py` | Parse and merge glossaries; give terms (L1) and replacement rules (L2) |
| `bias.py` | Build `hotwords` / `initial_prompt` within Whisper's prompt budget (about 224 tokens), terms ranked by priority |
| `fix_rules.py` | L2: explicit replacements, plus fuzzy matching of low-confidence words (difflib on accent-folded text, configurable threshold) |
| `llm.py` | L3: OpenAI-compatible chat client (stdlib `urllib`, no SDK), JSON mode, batching with context lines, retries, timeout, cancel |
| `providers.json` (defaults) | Presets: ollama, lmstudio, llamacpp, openai, gemini, anthropic, openrouter (base URL, default model, how to get the key) |
| `align.py` | Re-time corrected text: diff old vs new words; replaced words inherit (and split) the time span of the words they replace |
| `suggestions.py` | Review document `<name>.review.json` (v1): id, segment index, times, before, after, source (`glossary` / `llm`), reason, status (pending/accepted/rejected) |
| `guard.py` | Reject LLM output that rewrites too much: a different line count, an edit distance above a threshold, or changed words outside the low-confidence or glossary area unless allowed |

### 3.3 Config (`config.json`, ADR-006)

```json
"review": {
  "profile": "auto",
  "mode": "suggest",
  "glossary_bias": true,
  "fuzzy_threshold": 0.82,
  "low_confidence": 0.5,
  "llm": {
    "enabled": "auto",
    "provider": "ollama",
    "base_url": "http://127.0.0.1:11434/v1",
    "model": "",
    "api_key_env": "",
    "batch_lines": 20,
    "context_lines": 2,
    "max_change_ratio": 0.35,
    "timeout_s": 120
  }
}
```

- `profile`: auto | light | standard | full.
- `mode`: suggest | auto.
- `llm.enabled`: auto | true | false. `auto` means "use the LLM when the server answers".
- `llm.model` empty means the provider's default, or the first model the server lists.
- **API keys are never stored in project files.** They come from an environment variable named in `api_key_env`, or later from the OS keychain.

### 3.4 CLI

- `flosub transcribe … --glossary FILE` → L1 during transcription (on by default when a glossary exists).
- `flosub review video.json [--glossary FILE] [--llm|--no-llm] [--mode suggest|auto] [--provider P --model M]` writes `video.review.json` (suggest) or updates the transcript (auto), with progress events (`review_progress`, `suggestion`).
- `flosub review apply video.review.json [--all | --ids 3,7]` updates the transcript and re-exports cues/SRT/VTT.
- `flosub transcribe … --review` chains it all in one command.
- `flosub llm check` tests the configured server and lists its models. It powers the UI's "Test connection" button.

### 3.5 Blender

- A **Glossary** sub-panel: shows the global and project glossary files, "Edit" opens the file, a quick "Add term" field, and a "Use glossary while transcribing" toggle (L1).
- A **Review** sub-panel:
  - "Review captions" runs `flosub review` in the background, with progress and cancel.
  - The suggestions list (UIList) shows before → after, source and reason, with ✓ / ✗ per item and "Accept all".
  - "Apply" changes the text of the affected caption strips **in place**, keeping the user's manual timing edits.
- **Preferences:** LLM provider and model (filled from `flosub llm check`), server URL, the name of the API key environment variable, a "Test connection" button, the review mode, and the profile.

### 3.6 "Add to glossary" in every interface (owner decision, 2026-10-25)

Accepted corrections are **not** added to the glossary automatically. Every client that talks to the engine (Blender now; the web GUI, Kdenlive and mobile later) must offer an explicit way to add a word to the dictionary:

- **Engine first (ADR-011):** `flosub glossary add "Term" [--project FILE | --global]` and `flosub glossary add "wrong -> right"`; the same operation in the local HTTP API (plan 05). Duplicates are ignored, and the file keeps the user's comments and order.
- **From a suggestion:** each suggestion has "Add to glossary", which adds the corrected term and optionally the `wrong -> right` pair.
- **From a caption:** the user selects a caption and chooses "Add to glossary…". A small dialog shows the caption's text in an editable field (Blender cannot read a text selection inside a strip), the user keeps only the word or term, and picks the project or the global glossary.
- **Feedback:** the UI says where the term was saved and that it applies from the next transcription or review onward.

## 4. Stages

- **3a. Glossary (L1 + L2) in the engine and CLI — done (step 18).** Glossary files, hotwords/initial_prompt, deterministic fixes, the review document, `review apply`, re-alignment. Works offline on CPU.
- **3b. LLM reviewer (L3) in the engine and CLI — done (step 19).** Findings below (§7). OpenAI-compatible client, provider presets, guard, batching, `llm check`, profiles. Tested with the owner's Ollama (`llama3.1:8b`, `qwen2.5-coder:7b`; try a general instruct model such as `qwen2.5:7b-instruct` too) and with a fake server in CI.
- **3b+. Glossary library** (§3.1b) in the engine, before the UI, so that 3c can build on it.
- **3c. Blender UI** for the glossary and the review (suggestions list, apply in place), with pt_BR, tests and a GUI walkthrough.

## 5. Open questions (to settle during the stages)

1. Default local model to recommend: compare quality and speed on real Portuguese and English clips in 3b.
2. Applying suggestions to strips the user already edited by hand: match on time and on the "before" text. If the strip text no longer contains "before", skip it and report.
3. Ollama keeps a model in VRAM for 5 minutes after a call. On 8 GB GPUs this can collide with the next Whisper run. Options: send `keep_alive: 0` through Ollama's native API, or document it.
4. ~~Should accepted fixes be added to the glossary automatically?~~ **Decided (owner, 2026-10-25): no.** Nothing enters the glossary automatically. Every interface must instead offer an explicit **"Add to glossary"** action (see §3.6).

## 6. Definition of done

- [x] On the owner's crochet video: with the glossary, `transcribe` gets "Enacles", "Beth" and "Poliéster" right without an LLM (L1 + L2) — step 18.
- [x] `flosub review` with Ollama runs, rewrites like "perfeito → perfeita", translations and invented words are rejected by the guard, word timings stay aligned (step 19). On the test video the glossary already fixed everything; the LLM added nothing useful (§7).
- [x] A weak profile (CPU, no LLM server) still runs L1 + L2 and reports that the LLM is unavailable, without failing (step 19, tested with an unreachable server).
- [ ] Blender: glossary editing, review with suggestions, accept/reject, apply in place, "Add to glossary" from a suggestion and from a selected caption (§3.6), pt_BR UI.
- [ ] Tests in CI (fake LLM server), docs (`PROJECT.md`, devlog, CHANGELOG), engine release.

## 7. Findings from stage 3b (2026-10-26, owner's crochet video, 88 segments, `llama3.1:8b` on the RTX 2070 Super)

- **Asking for all lines back failed:** the 8B model merged lines (21 of 24 returned) and whole batches were dropped. Now the model returns **only the changed lines, by number** (`{"fixes": {"7": "…"}}`); omitted lines are unchanged. No more count errors, and the answers are shorter.
- **The model rewrites a lot:** 20 changes were rejected without the glossary and 47 with it. They included grammar changes, deleted filler words ("Mas", "Aí", "para"), a translation ("fake" → "falso") and an invention pulled from the glossary ("o cenoura" → "a bolsa Beth").
- **Guard v2:** never accept deletions. The new text must resemble the old (similarity ≥ 0.5 after folding) unless only accents, case or punctuation change. The old words must be uncertain, or the new text a glossary term. With it, the final suggestions were exactly the 4 correct glossary ones.
- **Conclusion:** on this video the **glossary (L1 + L2) did all the useful work**; the 8B LLM added nothing that survived the guard. L3 stays optional (profile `full`). Open question 1 (§5) remains: try general instruct models (`qwen2.5:7b-instruct`, `gemma`), larger models, or cloud models, on more videos, before recommending L3.
- **Speed:** about 60 s for the first run (model load), about 20 s afterwards, for 88 segments. Ollama models are unloaded from VRAM after the review (`keep_alive: 0`).
