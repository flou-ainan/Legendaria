# Origin brainstorm (sanitized summary)

> A generic retelling of the exploratory conversation, held with Google Gemini, that led to this project. The original transcript stays private because it contains personal data; this summary keeps only the technical path and the lessons learned.

## Starting point

The author had long recorded lectures (around 50 minutes each) and wanted subtitles generated **locally**, on a desktop with an NVIDIA RTX GPU running Linux Mint, with no cloud service.

## 1. First attempt: Whisper through Ollama

- Ollama was already installed, but its service would not start: earlier manual cleanup had deleted its data directory. A clean reinstall fixed that.
- Community "Whisper" models for Ollama (for example `dimavz/whisper-tiny`) could be downloaded but not run: `unknown model architecture: ''`.
- **Lesson:** Ollama runs text LLMs in GGUF through llama.cpp. It is not a speech-to-text runtime.

## 2. Choosing a Whisper implementation

The options compared:

- **openai-whisper:** the reference implementation, with word timestamps.
- **faster-whisper:** CTranslate2, faster and lighter on VRAM.
- **WhisperX:** forced alignment for very precise word timings.

**faster-whisper** won.

## 3. Making faster-whisper work

- The pip package ships no CLI entry point, and `python -m faster_whisper` has no `__main__`. A small `argparse` script (`transcribe.py`) was written as a CLI.
- **First run on CPU (int8):** it worked, but slowly, and the long run gave no feedback, so a `tqdm` progress bar was added, driven by `info.duration` and the end time of each segment.
- **GPU run:** it crashed with `Unable to load any of {libcudnn_ops.so.9...}` and a core dump. The cuDNN libraries had been installed by pip under `site-packages/nvidia/cudnn/lib`, where the dynamic linker does not look. Adding that directory to `LD_LIBRARY_PATH` fixed it.
- **Result:** about 50 minutes of Portuguese audio transcribed in about **38 seconds** with the `base` model in fp16 (around 78× real time), with language detection at 99% confidence and an SRT file as output.

## 4. How does CapCut do it?

- **On mobile:** CapCut mostly uploads the compressed audio to its cloud ASR, which returns segments with word-level timings. Offline packs exist only on some high-end devices.
- **On desktop:** it can use the local GPU, much like the pipeline above.
- **What makes the "CapCut look":** per-word timings plus animated text styling.

## 5. Where to edit subtitles interactively?

- **`.ass` files** support rich styling and karaoke effects, but cannot be edited interactively. Rejected as the editor.
- **Kdenlive** (MLT XML, external scripts) and **OpenShot** (PyQt UI) were considered.
- **Blender's Video Sequence Editor** won:
  - Its whole UI is scriptable in Python (`bpy`).
  - Each subtitle can be a native **text strip**: click to fix the text, drag the edges to retime it, style it in the sidebar.
  - SRT/VTT can be exported straight from the strips, with no render.
  - Blender's renderer can burn styled subtitles into the video.

## 6. First add-on sketch

A minimal add-on with a "Subtitles" sidebar tab, a "Generate" operator, and "Export SRT/VTT" operators. Blender's bundled Python does not have faster-whisper or CUDA, so the add-on calls the external transcription script through `subprocess`, reads its JSON output, and creates text strips (seconds × fps → frames).

## 7. Mobile (parked)

A possible future direction: extract audio on the device, run whisper.cpp locally for offline use, or send the audio to a self-hosted API backed by the same engine. Out of scope for now.

## What became of it

These findings became plan 01 and ADRs 001–003 in this folder's sibling directories. Plan 01 also lists the bugs in the brainstorm's sample code that the real implementation fixes.
