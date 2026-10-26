# Step 27 — KI-001 second occurrence: Blender's sequencer cache, measured

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

The owner reported that Blender froze, with high RAM use, during the manual test. The findings went into `known-issues.md` (KI-001):

- **System logs:** no OOM-killer entry around 16:00. Swap was full.
- **`flosub` measured** under a memory cap (`systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=0 /usr/bin/time -v`): `base` peaked at 0.75 GB and `small` at 0.72 GB. The engine was not the cause this time.
- **Blender measured:**
  - the owner's autosave (`/tmp/62732_autosave.blend`, 1080p clip at 24 fps) was opened under Xvfb and the timeline played while RSS was sampled every second;
  - with the owner's cache limit of 4096 MB, RSS reached 5.0 GB in 5 s;
  - with the limit at 1024 MB, RSS stayed at 1.9 GB.
- **New mitigation idea:** the add-on checks the sequencer cache limit against the free RAM and offers to lower it.

Also from the same test session, not changed yet (waiting for the owner's full feedback):
- The `base` model **did** download (142 MB at 15:53) and was used (`"model": "base"`, CUDA) in the 16:00 run. It is only less accurate than `small` ("Nácliffe" vs "Naques", "polieste").
- The owner's new glossary "Mariana Enacles" is **empty**: it has only the header lines. Creating a glossary is not the same as adding a term to it, so the UI could make "Add to glossary" more prominent after creating one.

No code changed.

## How it was tested

The measurements above, run in the scratchpad with memory caps, so the desktop could not freeze again.
