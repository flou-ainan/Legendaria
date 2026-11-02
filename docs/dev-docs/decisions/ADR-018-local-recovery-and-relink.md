# ADR 018 — Local recovery copy and relinking a moved video

**Status:** accepted (owner decision on the video check, 2026-10-27)
**Date:** 2026-10-27
**Related:** ADR-016 (project file), ADR-017 (opening files), plan 07

## Context

The owner wants to be able to close the tab (or lose the power) and come back to everything as it was, and wants a clear path when the video was moved or removed. The project file never holds the video (ADR-016), only its name.

## Decision

- **Where the state lives:** the server already writes the project next to the video 400 ms after each edit, and holds no other editing state. The browser adds a **recovery copy** in IndexedDB (`legendaria` / `kv` / `last`): the project, the video's full path, duration and size, a `dirty` flag and a timestamp. It is written on every edit with `dirty = true` and again with `dirty = false` once the server confirms the save. IndexedDB, not localStorage, because a project with hundreds of cues and word timings outgrows localStorage's ~5 MB. Only the last work is kept.
- **Resume:** the start screen offers "Continue where you left off". It reopens the video by path. The browser copy replaces the server's project only if `dirty` (the last save did not finish) or the server has none; otherwise the server file wins, so edits made elsewhere are not overwritten.
- **Moved or removed video:** if the path is gone, the screen says so, keeps the subtitles, and asks for the video again. A replacement is accepted when:
  - its **duration** is within 0.5 s of the original, and
  - its **screen proportion** (width / height) is within 1 %.
  Resolution may differ: cue times depend only on the duration, and the `.ass` scales to the video's size, so a proxy or a re-export at another resolution works. The project then moves next to the new video.
- **Menu:** File (open video, open project, close, save now, download a copy of the project, export), panels (narrow screens) and the interface language. A hamburger on narrow screens. Opening a `.legendaria.json` through the file browser opens its video.

## Alternatives considered

- **localStorage only:** too small for long projects.
- **Also require resolution, frame rate or audio:** refuses proxies that work fine. Duration plus proportion already catches the wrong video; a stricter check can be added if it proves too loose.
- **Server-side session state:** the server stays stateless between requests except for the open video.

## Consequences

- Clearing site data loses the recovery copy only; the project file next to the video stays.
- If a different video of the same length and proportion is chosen, the subtitles will not match what is said. The check cannot catch that; the preview shows it at once.
