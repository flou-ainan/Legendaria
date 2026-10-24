# Legendária

**English** | [Português (Brasil)](README.pt-BR.md)

**Free subtitles, CapCut style.** Free, open-source automatic subtitles for your videos, inspired by CapCut's auto captions.

*Legendária* blends the Portuguese word *legenda* (subtitle) with *legendary*. Its command-line tool is called `flosub`.

> 🚧 Early development. Nothing to install yet.

## What it will do

- **Transcribe automatically**, on your own computer (GPU-accelerated when available, CPU otherwise). No cloud, no account, no telemetry.
- **Edit visually in Blender:** every subtitle is a block on the timeline. Click to fix the text, drag to adjust the timing, style it your way.
- **Export** SRT/VTT for YouTube and other platforms, or render the video with the subtitles burned in.
- **Word-by-word animated captions** (CapCut style), coming after the first version.

## Goals

- A simple installer: next → next → finish, open Blender, drop your video in, click **Generate subtitles**.
- Runs on **Linux, macOS and Windows 10+**.
- Available in **English and Brazilian Portuguese**. More languages are welcome.
- **Hackable:** defaults, models, style presets and translations live in JSON files you can edit.

## Status and roadmap

See the [plan](docs/dev-docs/planning/plan_01_mvp_engine_blender.md) for the roadmap. A documentation website and a video tutorial will come with the first release.

## Contributing

Contributions are welcome, including translations. Start with [AGENTS.md](AGENTS.md) and [docs/PROJECT.md](docs/PROJECT.md): together they explain the project layout, the conventions and the current work.

## License

- Transcription engine and repository: [MIT](LICENSE)
- Blender add-on: GPL-3.0-or-later (required by Blender's extensions platform)
