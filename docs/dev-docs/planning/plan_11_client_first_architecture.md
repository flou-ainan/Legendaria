# Plan 11 — Client-first architecture (less network, one session per device, PWA autonomy)

**Status:** proposed (owner approved the scope on 2026-10-28)
**Related:** plan 08 (PWA section), ADR-014, ADR-016, step 50 (tunnels), plan 10

## Why

Testing through a tunnel exposed two design problems:

1. **The video travels back.** The phone uploads the file, the server sends the same bytes back to play it, and a second device pulls it again. A free ngrok account ran out of bandwidth (`ERR_NGROK_725`).
2. **One open video for the whole server.** `Session` is global, so every client sees the video another client opened, and two clients editing the same project overwrite each other.

Goal: the user's own editor, tied to their computer, that spends little network, keeps working when the server is away for what the browser can do alone, and grows without a rewrite (more devices, more local processing later).

## A. Play the local file, do not download it back

- When the video was picked on the device (a `File`), play it with `URL.createObjectURL(file)`; keep the upload only for what needs the server (transcription, export).
- Keep the `File`/`Blob` across reloads in OPFS (or IndexedDB) so a reload does not need the upload again.
- On the computer that runs the server, keep streaming from the server (no extra copy).
- Done when: a phone session moves the video once (the upload), and playing, seeking and editing cost no video bytes.

## B. One session per client

- The browser creates an id (stored with the project in `localStorage`/IndexedDB) and sends it on every request; the server keeps a map `id -> Session` (video, jobs, lock) instead of one global `Session`.
- Opening a video in one client never changes another client's view. Two clients opening the same project file get a clear warning instead of a silent overwrite (a lock or a version check on save).
- Server restarts must not lose anything: sessions are rebuilt from the project file on demand.
- Needs an ADR (API contract change, bump `API_VERSION`).

## C. Move to the client what the browser can do alone

Order matters: each step is useful by itself and leaves the server path working.

1. **A backend interface in the web app** (`lib/backend.ts`): `media`, `peaks`, `previewAss`, `project load/save`, `transcribe`, `export`. Today's HTTP calls become the "server" implementation; a "local" one can be added beside it. The editor talks only to the interface.
2. **`.ass` generation in TypeScript**, a port of `ass.py`, checked against golden `.ass` files produced by the Python code (same input, same output) so the preview and the export cannot drift.
3. **Peaks in the browser** (Web Audio / WebCodecs decode of the local file) instead of `/api/peaks`.
4. **Project storage on the device** (OPFS/IndexedDB) with explicit import/export of the `.legendaria.json`; the server copy becomes a sync target, not the only truth.
5. **Installable PWA shell** (plan 08): manifest, service worker, the app files cached, so the editor opens and edits without the server and only needs it for transcription and export.
6. **Research spike, not committed:** transcription and export on the device (Whisper in WASM/WebGPU, WebCodecs for cut + burn). Measure speed, memory and quality of Portuguese before planning anything.

Stays on the server in this plan: transcription (faster-whisper), export (FFmpeg), glossary review, font bundle.

## Order

A and B first (they fix real bugs and shrink traffic), then C1, C2, C3, C4, C5. C6 whenever the owner wants to evaluate it.

## Not in scope

Accounts, payments, store packaging.
