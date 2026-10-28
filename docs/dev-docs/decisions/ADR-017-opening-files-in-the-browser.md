# ADR 017 — Opening a video from the browser

**Status:** accepted (agent proposal, applied after the owner asked for "open a file or drag a video")
**Date:** 2026-10-27
**Related:** ADR-014 (web editor + local server), ADR-016 (project file next to the video), plan 07

## Context

The owner wants `flosub serve` to run without a path, and the start screen to offer two ways to load a video: choose a file, or drop it on the page.

A web page never learns the path of a file the user picks or drops (`<input type="file">`, drag and drop and the File System Access API only give a `File` object). The server runs on the same computer and needs a real path for FFmpeg, for the project file next to the video (ADR-016) and for the exports.

## Decision

- **Choose a file:** a file browser dialog inside the page, backed by `GET /api/browse?path=` (folders and media files only, hidden entries skipped, an editable folder path). The chosen path goes to `POST /api/open`. The video is opened **in place**, with no copy, and the project and exports land next to it.
- **Drop a file:** the page uploads the `File` (`POST /api/upload?name=`, streamed in 1 MB chunks, progress through XHR) to `<data dir>/uploads/<id>/<name>` and opens that copy. The project and exports then live in that folder. The start screen says so.
- Both routes are available only to local requests (the Host/Origin guard of ADR-014).

## Alternatives considered

- **Always upload:** one path to maintain, but it duplicates every video (often gigabytes) and hides the project from the user.
- **Only the path as text:** simple, but not what the owner asked for.
- **A native dialog from Python (tkinter):** blocks the server thread, is missing on some Linux installs, and does not match the web look.
- **A desktop wrapper (Tauri/Electron) later:** a native dialog gives the real path and drag and drop in a wrapper often does too. Kept as a future option; the routes stay valid.

## Consequences

- The dropped-file copy can be large. Cleaning old uploads is not automated yet; they are plain folders under the data dir.
- The file browser lists the computer's folders to whoever can reach the server, which is why the local-only guard matters and why the server must keep listening on 127.0.0.1 only.
- On Windows the browser starts at the home folder and has no drive list yet; typing a path (for example `D:\Videos`) works.
