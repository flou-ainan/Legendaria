# ADR 001 — faster-whisper as the transcription engine

**Status:** accepted
**Date:** 2026-10-23

## Context

We need local speech-to-text, in Portuguese and other languages, with a timing for every word (the base for CapCut-style animated captions). It has to use the local GPU when there is one; the reference machine has an RTX 2070 Super with 8 GB.

## Decision

Use **faster-whisper** (Whisper on CTranslate2): fp16 on NVIDIA GPUs, int8 on CPU as the fallback. The default model is `small`; other models can be downloaded from the app.

## Alternatives considered

- **Ollama + community Whisper models** (`dimavz/whisper-tiny`): rejected. Ollama runs text GGUF models through llama.cpp and fails with `unknown model architecture`. Tested in the origin brainstorm.
- **openai-whisper** (the reference implementation): slower, uses more VRAM, and depends on PyTorch.
- **WhisperX:** more precise word timings (forced alignment with wav2vec2), but a heavier install. A possible upgrade if faster-whisper's word timings fall short.
- **whisper.cpp / mlx-whisper:** strong on Apple Silicon and mobile. Candidates for a second backend on macOS (ADR-007).

## Consequences

- Measured: 49 min of audio in about 38 s with `base` on the GPU.
- CTranslate2 needs cuDNN 9 and cuBLAS 12 to be visible to the dynamic loader. The engine handles this itself (plan 01).
- No PyTorch.
- CTranslate2 has no GPU backend on macOS, so Mac runs on CPU unless a second backend is added.
