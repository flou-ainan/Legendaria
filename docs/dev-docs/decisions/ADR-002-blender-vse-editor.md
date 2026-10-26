# ADR 002 — Blender's VSE as the interactive subtitle editor

**Status:** superseded by ADR-014 (web editor; the add-on is frozen)
**Date:** 2026-10-23

## Context

The target experience is CapCut-like: generate subtitles automatically, then **edit them interactively** (fix text, adjust timing, style them), and also export subtitle files.

## Decision

Build a **Blender extension** (add-on) for the Video Sequence Editor, supporting Blender **4.2 and newer**. Each subtitle is a native text strip on the timeline. SRT/VTT export reads the strips and needs no render.

## Alternatives considered

- **Generate `.ass` and burn it with FFmpeg:** supports styles and karaoke, but offers no interactive editing. It may still become an extra export or burn-in path.
- **Kdenlive:** mature, with its own speech-to-text, but extending it means external scripts and editing MLT XML, with no rich UI API.
- **OpenShot:** Python UI, but a limited text engine.
- **Our own editor:** far too much work for the MVP.

## Consequences

- Blender provides the UI, timeline, preview, and rendering for free, on all three OSes.
- Blender's bundled Python lacks the engine's dependencies, which leads to ADR-003.
- The VSE API changes between versions (`sequences` → `strips` from 4.4 on), so all access goes through a compatibility module.
- Extensions on the official Blender platform must be GPL-3.0-or-later (ADR-004).
