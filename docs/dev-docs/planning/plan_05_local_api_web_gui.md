# Plan 05 — Local HTTP API and the `flosub gui` web interface (draft)

**Status:** draft
**Date:** 2026-10-25
**Related decision:** ADR-011

Scope:
- **Local HTTP API** over the engine core: start and cancel jobs, server-sent events for progress, models, glossary, review suggestions. Bound to `127.0.0.1` only.
- **`flosub gui`:** a web interface (plain HTML/CSS/JS, no build step) served by the API and opened in the default browser:
  - pick a file → transcribe → review suggestions → edit captions → export SRT/VTT;
  - manage models and glossaries;
  - English and pt-BR.
- **Native window (optional):** `flosub gui --window` through `pywebview`. The owner wants it after the MVP, unless it turns out trivial; on Linux it needs GTK/WebKit or Qt system libraries, which the installer cannot guarantee, so it is planned as an optional extra.
- Future clients reuse the API: Kdenlive integration, mobile.

To be detailed before implementation.
