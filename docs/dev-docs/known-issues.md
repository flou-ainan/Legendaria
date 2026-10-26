# Known issues

Problems seen in real use that are not fixed yet. Each entry has the evidence, the hypotheses and how to investigate it. When one is fixed, link the devlog step and move it to the "Resolved" section.

## KI-001 — PC froze (RAM exhausted) when choosing the `medium` model in Blender

**Reported:** 2026-10-26 by the owner. **Priority:** high: it froze the whole desktop and needed a hard reboot.

**What the owner saw:** in Blender 5.2 the owner picked `medium` (not yet downloaded) and pressed Generate. The UI was still showing the download. The system monitor attributed about **5.3 GB of RAM to Blender**; then the PC froze and had to be restarted.

**Evidence collected after the reboot:**
- The download **had finished**: `~/.local/share/legendaria/models/medium/model.bin` is complete (1,527,906,378 bytes, written at 10:29), and `flosub models list` shows `medium` as installed.
- The previous boot's journal ends at **10:29:43**, right after the download finished. There was **no OOM-killer entry** at that time. An earlier OOM event at 05:29 killed Chrome while Kdenlive was allocating.
- Machine: 15 GiB of RAM, **only 2 GiB of swap** (`/swapfile`, swappiness 60), RTX 2070 Super with 8 GB. Blender, Kdenlive and Chrome were probably open.

**Hypotheses, to verify:**
1. **Model loading, not the download.** After the download, `flosub` immediately loads `medium` into CTranslate2. Loading reads the file into RAM and converts it (float16 on CUDA, int8 on CPU), and the peak RSS may be 2–3× the model size (about 3–5 GB), which matches the 5.3 GB reading.
2. **Attribution:** system monitors usually add child processes to their parent, so the 5.3 GB was probably the `flosub` child, not Blender itself.
3. **No room left:** with other heavy apps open and only 2 GiB of swap, the system started thrashing before the kernel could pick an OOM victim, so the desktop froze instead of one process being killed.
4. **A GPU fallback could make it worse:** if the CUDA load failed, the `auto` mode retries on CPU (`int8`), which loads the model again in RAM. To be checked in the event log.
5. Less likely: the download itself (Hugging Face transfer buffers), or the add-on's event queue. Both are throttled and bounded; to be ruled out by measurement.

**How to investigate (safely, inside a memory cap so the PC cannot freeze):**
- Run `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 /usr/bin/time -v flosub --progress json transcribe clip.mp3 --model medium` and record "Maximum resident set size", for CPU and GPU, for `small`, `medium` and `large-v3-turbo`.
- Sample RSS every 0.5 s during download → load → transcribe, to see which phase peaks.
- Same test from Blender, watching the Blender and `flosub` PIDs separately.

**Possible mitigations (after measuring):**
- Add `ram_mb` (peak) to `models.json`; the engine and the add-on check available RAM before loading and refuse or warn with a clear message ("medium needs about X GB of free RAM; close other programs or choose small").
- The UI shows the "Loading model…" phase explicitly (the status may still have said "downloading").
- Run the engine with lower priority and, on Linux, optionally in a memory-capped scope, so a spike kills the transcription instead of freezing the desktop.
- Check CTranslate2 load options (for example `int8_float16`) for a lower peak.
- Recommend a larger swap in the docs for 16 GB machines.

## Resolved

(none yet)
