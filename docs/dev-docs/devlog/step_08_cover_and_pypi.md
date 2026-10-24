# Step 08 — Social preview cover and PyPI release workflow

**Date:** 2026-10-24
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

- **Cover:**
  - The owner reviewed five social-preview variants (banner, bilingual, centered, "pitch", flat) and chose the **pitch** layout: glowing symbol, wordmark, tagline, two lines saying what the project does, and the repo link in a pill.
  - Added it to `generate_hero.py` as `cover(lang)`, with localized `PITCH` lines (en / pt-BR), exported as `cover-<lang>.svg` (text converted to paths) and `png/social-preview-<lang>.png`.
  - The upload to GitHub Settings is manual (there is no API for it).
- **PyPI:**
  - The owner created the PyPI account (2FA on) and a **pending trusted publisher**: project `legendaria`, repo `flou-ainan/Legendaria`, workflow `release.yml`, environment `pypi`.
  - PyPI warns that a pending publisher does **not** reserve the name, so the first release is what reserves it.
- **`.github/workflows/release.yml`:**
  - Runs on `v*` tags.
  - Checks that the tag matches the engine version, runs the tests, and builds the sdist and wheel with `uv build`.
  - Publishes through `pypa/gh-action-pypi-publish` with OIDC (`id-token: write`).
  - Actions are pinned to releases at least two weeks old.
- **GitHub environment `pypi`:** only `v*` tags may deploy to it.
- **Docs:** "Releasing" section in `CONTRIBUTING.md`, brand README, `PROJECT.md`, `CHANGELOG.md`.

## How it was tested

- `uv build` locally: the wheel contains the defaults JSON, the MIT license, the `cuda`/`test` extras and the `flosub` entry point.
- The release itself: tag `v0.1.0.dev0` after this PR is merged (result recorded below).

## Release result

- Tag `v0.1.0.dev0` on `d8054c4`. The `Release` run (id 40070081622) built and published successfully.
- https://pypi.org/project/legendaria/ now lists `0.1.0.dev0`: **the name is reserved**. It is a pre-release, so a plain `pip install legendaria` will not pick it up by accident.
- Verified from a clean environment: `uvx --isolated --from legendaria==0.1.0.dev0 flosub --version` → `flosub 0.1.0.dev0`, and `models list` works.
- GitHub pre-release created for the tag.
