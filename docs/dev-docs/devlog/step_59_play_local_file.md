# Step 59 — Play the device's own file (plan 11, item A)

**Date:** 2026-10-28
**Related:** plan 11, step 58

- **Why:** a video picked on the phone was uploaded and then streamed back by `/api/media` to be played, so it crossed the network twice (the cause of the ngrok bandwidth limit).
- **What:** `lib/localmedia.svelte.ts` keeps an object URL of the uploaded `File`. `uploadVideo` sets it when the upload succeeds, `openVideo` clears it (a file on the computer is still streamed by the server). `Player.svelte` uses `localMedia.url ?? '/api/media'` and skips the "is the file missing on the server" probe while it plays the local file. The upload stays: transcription and export need the file on the computer.
- **Not done:** the file is not kept across a reload (after one, the server's copy is streamed). OPFS storage is the next part of item A.
- **Tests:** e2e drops a file in a second browser context (its own session) with the upload response stubbed to carry the fixture project; it checks that the `<video>` source is a `blob:` URL and that no `/api/media` request is made, even after a seek. svelte-check 0 errors, Vitest 11, e2e ok (run `npm run build` first: the server serves the built files). Not tried on a real phone.
