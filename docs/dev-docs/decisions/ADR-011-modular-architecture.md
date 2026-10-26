# ADR 011 — Modular architecture: engine core, access layers, clients

**Status:** accepted
**Date:** 2026-10-25

## Context

Blender is only the first interface. The owner also edits in Kdenlive and wants `flosub` to have its own simple GUI and, later, mobile support. Features such as the reviewer touch both the engine and every UI.

## Decision

Three layers, each depending only on the one below:

1. **Engine core** (`legendaria_engine`, MIT): transcription, cues/styles, glossary and review, file formats. A plain Python API with no UI code.
2. **Access layers**, thin wrappers over the core:
   - the **CLI** (`flosub`, JSON-lines events);
   - a **local HTTP API** (plan 05): JSON plus server-sent events for progress, bound to localhost.
3. **Clients:**
   - the **Blender add-on** (GPL; talks to the CLI, ADR-003);
   - the **web GUI**, `flosub gui`: HTML/CSS/JS served by the local API and opened in the browser (plan 05). An optional native window through `pywebview` is an extra after the MVP, because on Linux it needs system web-view libraries;
   - later: Kdenlive integration, mobile.

Rules:
- Features are implemented in the core first, exposed through the CLI (and API), and only then wired into the clients. Clients never re-implement engine logic.
- Contracts are versioned JSON (transcript, cues, review, events) with published schemas.

## Consequences

- Each client stays small. A new client (for example Kdenlive) only needs the CLI or the API.
- The web GUI and the HTTP API come together in plan 05; the review UI in Blender (plan 03) uses the CLI.
