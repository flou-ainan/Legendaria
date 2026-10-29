# Roadmap

**The one list of what is left.** Start here, not in the latest plan. Each item points to the plan that holds its details. When an item is done, move it to "Done" with its step number; when a plan is finished, set its status line to `done`.

**Last updated:** 2026-10-29 (plan 13 added). **The "Before the MVP" column is a proposal; the owner confirms it.**

## Before the MVP (proposed)

| Item | Plan | Notes |
|---|---|---|
| **UX identity (the essence of the project):** phone clones InShot / CapCut, desktop feels like Kdenlive with its shortcuts | 13 | Draft; step 0 is research with the owner's screenshots. Replaces the old "touch dragging" item: block dragging and the rest of the touch feel are part of it. |
| Warn when two browsers open the same project file | 11 (B) | Sessions are per browser already (step 57). |
| LAN mode (listen on the local network, opt-in) | 12 (1) | ADR-024. |
| Login with user name and password | 12 (2) | Needs a threat model first; required once the server listens beyond localhost. |
| "Use it from your phone" in the READMEs (LAN, then Tailscale) | 12 (3) | en + pt-BR. |
| Import `.ass` / `.srt` and align | 04 §11.3 | Owner decision pending. |
| Test on a real phone: video from the device, Save to this device, desktop extras | 10, 11 | Owner tests, then sends corrections. |

## After the MVP

| Item | Plan | Notes |
|---|---|---|
| Keep the device's video across reloads (OPFS) | 11 (A) | After a reload the server's copy is streamed. |
| Projects folder: list, switch, create from the phone | 11 (E) | To refine: does the video move into the folder? where is the folder? |
| Installable PWA shell (manifest, service worker, fluidity checklist) | 08 | HTTPS needed (Tailscale gives it). |
| Several subtitle tracks | 08 | Project file version bump + ADR. |
| "Voice only" as a caption source | 08 | |
| Interactive tutorial | 08 | The permanent tips were removed in step 36. |
| Reorganize, slim the code, end-user installer ("next > next") | new plan | Owner, 2026-10-28. |
| Fonts on Windows and macOS, drive list on Windows, cleaning old uploads | 07 | |
| LLM pass in the review panel (experimental) | 03 | Off by default. |
| Engine release to PyPI | 03 | The tag needs the owner's approval. |

## Ideas (not decided)

| Idea | Plan |
|---|---|
| Client-side work: backend interface, `.ass` in TypeScript, peaks in the browser, local project storage, on-device transcription spike | 11 (C), postponed |
| Stickers, effects, multiple video tracks, animations | 08 "Not now" |
| More animations (CapCut look) | 04 |

## Done (recent)

Web editor MVP (steps 31–33), look and fonts (35, 42–46), contextual toolbar (36), phone layout and sheets (47–49), tunnels (50–51), desktop extras (52–53), phone fixes (54–56), one session per browser (57), files on both sides (58), local playback of the device's video (59).

## Plans at a glance

| Plan | Status |
|---|---|
| 01–03, 09, 10 | done |
| 04 | MVP subset done; the rest is after the MVP |
| 05, 06 | superseded by 07 |
| 07 | web editor: MVP done, owner testing; leftovers are in the tables above |
| 08 | reference for the UX study and the PWA; its open items live here |
| 13 | draft: UX identity (InShot / CapCut phone, Kdenlive desktop); research first |
| 11 | A, B, D mostly done; E and C after the MVP |
| 12 | LAN and login; open |
