# Legendária engine (`flosub`)

The transcription engine of [Legendária](https://github.com/flou-ainan/Legendaria): it runs Whisper (faster-whisper) locally and writes subtitles with per-word timings. The Blender add-on uses it, and it also works on its own:

```bash
flosub transcribe video.mp4                  # writes video.json, video.srt, video.vtt
flosub transcribe talk.mp3 --language pt --model medium --format srt
flosub export video.json --format vtt
flosub models list
flosub models download medium
flosub config show
```

GPU acceleration works on NVIDIA cards (Linux and Windows) with the `cuda` extra; everything else runs on the CPU.

## Development

```bash
cd engine
uv sync --extra test             # add --extra cuda for NVIDIA GPUs
uv run flosub --help
uv run pytest
```

License: MIT.
