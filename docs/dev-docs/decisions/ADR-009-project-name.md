# ADR 009 — Project name: Legendária, with the `flosub` command

**Status:** accepted
**Date:** 2026-10-24

## Context

The working name "Open Subtitler" was easy to confuse with OpenSubtitles.org, a large brand in the same field, and its short form `opensub` was already in use (opensub.in). The owner wanted a name that is memorable as a product and quick to type as a tool.

## Decision

- **Product / display name:** **Legendária**. It blends the Portuguese *legenda* (subtitle) with *legendary*, so it carries a Brazilian identity and still reads well in English.
- **Slogan:** "Legendária — free subtitles, CapCut style" / "legendas livres, estilo CapCut".
- **Technical identifiers** (no accent, so URLs, file systems and package indexes all accept them):
  - GitHub repository: `flou-ainan/Legendaria`
  - Python distribution: `legendaria` (free on PyPI); import package `legendaria_engine`
  - Blender add-on id and per-OS config/data dir names: `legendaria`
- **CLI command:** **`flosub`**. It is short and easy to type, and it nods to FLOSS (*Free/Libre Open Source Software*) and to the creator's name (Flou).

## Alternatives considered

Checked on 2026-10-24 on PyPI, on GitHub and on the web:

- **Open Subtitler:** risk of brand confusion.
- **SubFlow:** taken on PyPI; an active AI subtitle tool with the same name exists on GitHub.
- **VoxCut:** a commercial video tool with the same name exists (voxcutpro.com); taken on PyPI.
- **vocut:** an existing voiceover video editor, and almost the same sound as VoxCut.
- **subx, legio, subforge, captionforge:** taken on PyPI or crowded.
- **SubStrip, WordCue:** free, but too niche (Blender-only) or too generic.
- **Kaption:** too close to an existing local Whisper subtitle tool.
- **Any name containing "Blender":** restricted by the Blender Foundation's trademark policy.
- **`lgd` as a short alias for Legendária:** works, but `flosub` is more memorable.

## Consequences

- There are two names to explain (product and command). The READMEs explain both in their first lines.
- The PyPI name `legendaria` should be reserved early, with a first release or a placeholder.
- The old GitHub URL (`Open-Subtitler`) redirects to the new one. The local checkout folder name does not matter.
- The devlog keeps the old name in steps 00–03 as history.
