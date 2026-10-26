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

## Future: a full web subtitle editor (owner brainstorm, 2026-10-26, beyond the MVP)

Kept here for later; nothing is decided.

- **Why web instead of a Kdenlive fork:**
  - Kdenlive is a large C++/Qt code base, while a web editor grows out of this plan's `flosub gui`;
  - contributors know web tech;
  - it reaches phones and tablets more easily (a PWA).
  - On a phone, transcription still needs an engine: whisper.cpp / WebAssembly on the device, or the desktop engine over the local API on the same network.
- **Exact rendering in the browser:**
  - libass compiled to WebAssembly (projects such as JASSUB or SubtitlesOctopus) draws `.ass` over an HTML5 `<video>` in real time, with the same renderer as `flosub burn`. No server round-trip per frame is needed.
  - Frame-by-frame stepping and precise seeking still need care, because browsers seek to keyframes.
- **Data model:**
  - the `.ass` structure: Script Info, Styles, Events, and the override tags of each event parsed into blocks;
  - Aegisub's code (its file / style / dialogue classes and its override-tag parser) can inspire how to edit properties through a friendly UI. Aegisub is mostly under the 3-clause BSD license, with some parts under other permissive licenses (owner's research, 2026-10-26). Studying its design and taking inspiration is free. If code is ever copied, check the license of that specific file and keep its notice;
  - in Python, `pysubs2` (MIT) already reads and writes `.ass` if the engine ever needs to.
- **MVP of that editor:**
  - a video with an exact libass preview, a timeline of events, and a properties panel for every `.ass` style and tag;
  - start with the tags our styles use (position, scale, colors, fades, `\t`), then grow with the community.
- **Mobile:** still out of scope for now (the plan 01 decision). This is the most plausible route when it comes back.
