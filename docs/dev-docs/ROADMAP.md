# Roadmap

**The one list of what is left.** Start here, not in the latest plan. Each item points to the plan that holds its details. When an item is done, move it to "Done" with its step number; when a plan is finished, set its status line to `done`.

**Last updated:** 2026-11-02 (access decision, step 61).

**Focus (owner, 2026-10-31):** tie together what already works, then fix what the owner lists. No new features until then. The product direction (CapCut / InShot feel on the phone) is in `AGENTS.md`; it is not a work item.

## Now: put the house in order (plan 15)

| Item | Plan | Notes |
|---|---|---|
| Get what exists into `main`: push, CI green, merge #28 and then #29 | 15 | Needs the owner's approval. Lint fixed in step 60. |
| **Network access:** LAN by default with a password for every non-local access, a tkinter launcher, docs in en + pt-BR | 12 | Decided (ADR-026, 2026-11-02). Seven steps; the core (`access.py`) and the server gate are security-sensitive. |
| Test on a real phone: video from the device, Save to this device, desktop extras | 10, 11 | Owner tests. |

## Next: the owner's corrections

The owner will send a list of what is not good yet, once the items above are closed. It comes before everything below.

## Parked (start only when the owner asks)

| Item | Plan | Notes |
|---|---|---|
| Raw subtitles + effects | 14 | ADR-025 is still proposed. It changes the project file, so it should come before large UI work on cues. |
| Warn when two browsers open the same project file | 11 (B) | Sessions are per browser already (step 57). |
| Import `.ass` / `.srt` and align | 04 §11.3 | Owner decision pending. |
| Keep the device's video across reloads (OPFS) | 11 (A) | After a reload the server's copy is streamed. Needs HTTPS. |
| Projects folder: list, switch, create from the phone | 11 (E) | To refine: does the video move into the folder? where is the folder? |
| Installable PWA shell (manifest, service worker, fluidity checklist) | 08 | Needs HTTPS. |
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

Web editor MVP (steps 31–33), look and fonts (35, 42–46), contextual toolbar (36), phone layout and sheets (47–49), tunnels (50–51), desktop extras (52–53), phone fixes (54–56), one session per browser (57), files on both sides (58), local playback of the device's video (59), roadmap reorganized and lint fixed (60), network access designed (61, docs only).

## Plans at a glance

| Plan | Status |
|---|---|
| 01–03, 09, 10 | done |
| 04 | MVP subset done; the rest is parked |
| 05, 06 | superseded by 07 |
| 07 | web editor: MVP done, owner testing; leftovers are in the tables above |
| 08 | reference for the UX study and the PWA; its open items live here |
| 11 | A, B, D mostly done; E and C parked |
| 12 | network access: approved (ADR-026), not started |
| 13 | abandoned: became the product direction in `AGENTS.md` |
| 14 | parked: raw subtitles + effects (ADR-025 proposed) |
| 15 | in progress: house in order |
