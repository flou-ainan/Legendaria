# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Transcription engine `flosub` (package `legendaria`): local faster-whisper transcription on NVIDIA GPU (fp16) or CPU (int8) with automatic GPU→CPU fallback; per-word timings; JSON (v1), SRT and VTT output; `export`, `models list|download` and `config show|path` commands; layered JSON config and model catalog with JSON Schemas; JSON-lines progress events for the Blender add-on.
- `tools/project_map.py` to generate the file map of `docs/PROJECT.md`.
- Project documentation: README (en / pt-BR), plan 01, ADRs 001–009, devlog.
- Brand kit: glowing key art (en / pt-BR), flat symbol, icons, lockups, favicon.
- Contribution setup: CONTRIBUTING, Code of Conduct, security policy, issue and PR templates, ruff + pre-commit, CI on Linux / macOS / Windows.
