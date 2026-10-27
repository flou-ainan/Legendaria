# Step 41 — Generate captions sheet

**Date:** 2026-10-27
**Related:** plan 08

- `Transcribe.svelte` has a `sheet` mode: a modal over the editor (model, language, style, Generate, Cancel) opened from File → "Generate captions…". The first run still uses the full page.
- `server.py`: generating again keeps the previous project's `keep` (cuts) and `look`; only the cues are replaced.
- Strings in both locales (`menu.generate`, `transcribe.sheet_title`, `transcribe.replaces`, `cancel`).

Tested: svelte-check, Vitest 11, 130 pytest, e2e (the sheet opens from the menu and Cancel closes it). A real re-transcription from the sheet was not run (it needs a model); the keep-cuts logic is only read, not tested.
