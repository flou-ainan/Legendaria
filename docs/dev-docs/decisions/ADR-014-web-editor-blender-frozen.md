# ADR 014 — A web editor becomes the main interface; the Blender add-on is frozen

**Status:** accepted (owner, 2026-10-26)
**Date:** 2026-10-26
**Supersedes:** ADR-002 (Blender VSE as the editor). **Suspends:** ADR-013 (Blender 5.2 minimum).

## Context

The add-on made Blender's Video Sequence Editor the editing surface (ADR-002). In the owner's manual test it was too heavy for the job:
- a desktop freeze from RAM pressure (KI-001);
- caption strips that are hard to find and edit;
- an exact preview that has to render a `.mov`.

The owner needs only three things:
- cut the video;
- edit the subtitles;
- export burned-in video or SRT / VTT / ASS.

Meanwhile, every hard part already lives in the engine (`flosub`), behind a process boundary (ADR-003, ADR-011).

## Decision

- A **browser editor** served locally by the engine (`flosub serve`, 127.0.0.1) becomes the main interface (plan 07).
- The **Blender add-on is frozen**:
  - it stays in the repository, keeps working with the engine, and gets bug fixes only;
  - it gets no new features;
  - it will likely be removed once the web editor covers what the add-on does.
- **ADR-013 is suspended**, and the native pop on word strips (plan 04 §11.4) is not implemented.
- The exact preview moves to libass in WebAssembly (JASSUB). Burn-in and cuts run on the server with native FFmpeg.

## Alternatives considered

- **Keep improving the add-on:** it would reuse what exists. It was rejected because of Blender's weight and UX, which we cannot fix from an add-on.
- **Delete the add-on now:** a cleaner repository. It was rejected for now, because the add-on is the only visual UI until the web MVP works. Deleting it later is cheap and git keeps the history.
- **Fork Kdenlive:** a large C++/Qt code base (plan 05 brainstorm). It was rejected.

## Consequences

- New stack pieces: a JS/TS front end and a local HTTP server (ADR-015, written in phase 1 of plan 07).
- The licenses stay clean:
  - the engine is MIT;
  - the web UI is planned as MIT (to be confirmed in ADR-015);
  - the GPL add-on is isolated;
  - FFmpeg runs as an external program.
- CI keeps one Blender smoke job until the add-on is removed.
- Plans 05 and 06 are superseded by plan 07.
