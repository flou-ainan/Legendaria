# Plan 11 — Client-first architecture (less network, one session per device, PWA autonomy)

**Status:** in progress. A, B and D are the current scope; C is postponed (owner, 2026-10-28)
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
- **Status:** the per-browser session is done (step 57, ADR-023, a cookie instead of a header so `<video>` and `EventSource` carry it). The warning for two browsers on the same project file is still open.

## D. Files from both sides, results to both sides (added 2026-10-28)

The focus of the open project is local use: the editor runs on the user's computer and the phone is another screen for it (over Tailscale or a tunnel). Full independence of the phone is not a goal for now.

- **Open from the computer or from the phone.** On a phone the start screen and File ▸ Open offer both: "Computer files" (the server's file browser, nothing is uploaded) and "This device" (the phone's picker, the video is uploaded).
- **Save to the computer or to the phone.** Exports are written next to the source on the computer as today, and each finished export also offers "Save to this device" (a download of the same file). The project file (`.legendaria.json`) can be downloaded too (already in the File menu).
- Uploaded files stay in the uploads folder on the computer and can be opened again from "Computer files".
- Done when: from the phone alone the owner can edit a video that lives on the computer, or one from the phone, and end up with the result on either side.

**Status:** open from either side and "Save to this device" are done (step 58); not tried on a phone yet.

## E. A projects folder (owner idea, 2026-10-28; to refine before building)

Keep the projects in one folder on the computer, with a list to open and switch between them, and let the phone create new ones. Today a project is a `<video>.legendaria.json` next to its video. Open questions: does the video move into the project's folder or stay where it was, and where is the folder (a setting)?

## C. Move to the client what the browser can do alone (postponed)

Not in the current scope: the owner prefers to keep the project local-first and to revisit phone independence when the project is mature (an installable shell, local storage and on-device processing included). The list is kept as the starting point.

Order matters: each step is useful by itself and leaves the server path working.

1. **A backend interface in the web app** (`lib/backend.ts`): `media`, `peaks`, `previewAss`, `project load/save`, `transcribe`, `export`. Today's HTTP calls become the "server" implementation; a "local" one can be added beside it. The editor talks only to the interface.
2. **`.ass` generation in TypeScript**, a port of `ass.py`, checked against golden `.ass` files produced by the Python code (same input, same output) so the preview and the export cannot drift.
3. **Peaks in the browser** (Web Audio / WebCodecs decode of the local file) instead of `/api/peaks`.
4. **Project storage on the device** (OPFS/IndexedDB) with explicit import/export of the `.legendaria.json`; the server copy becomes a sync target, not the only truth.
5. **Installable PWA shell** (plan 08): manifest, service worker, the app files cached, so the editor opens and edits without the server and only needs it for transcription and export.
6. **Research spike, not committed:** transcription and export on the device (Whisper in WASM/WebGPU, WebCodecs for cut + burn). Measure speed, memory and quality of Portuguese before planning anything.

Stays on the server in this plan: transcription (faster-whisper), export (FFmpeg), glossary review, font bundle.

## Order

A, B and D now (real bugs, less traffic, the files flow the owner asked for). C only when the owner asks.

## Not in scope

Accounts, payments, store packaging.
