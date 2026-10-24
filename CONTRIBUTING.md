# Contributing to Legendária

Thanks for helping! Every contribution counts: code, translations, docs, bug reports, testing on your OS or GPU. You can write issues and discussions in **English or Portuguese**. Code, commits and developer docs are in English.

## Before you start

- Read [`AGENTS.md`](AGENTS.md) (rules for humans and AI agents alike) and [`docs/PROJECT.md`](docs/PROJECT.md) (the project map).
- See what is in progress in [`docs/dev-docs/`](docs/dev-docs/): `planning/`, `devlog/` and `decisions/`.
- Looking for something to do? Try issues labeled [`good first issue`](https://github.com/flou-ainan/Legendaria/labels/good%20first%20issue) or [`help wanted`](https://github.com/flou-ainan/Legendaria/labels/help%20wanted).
- For larger changes, open an issue or a discussion first, so we can agree on the approach.

## Setup

You need git, [uv](https://docs.astral.sh/uv/) and, for the add-on, Blender 4.2 or newer.

```bash
git clone https://github.com/flou-ainan/Legendaria.git
cd Legendaria
uvx pre-commit install        # runs ruff and other checks on every commit
```

### Engine (`engine/`)

```bash
cd engine
uv sync --extra test          # add --extra cuda on Linux/Windows with an NVIDIA GPU
uv run pytest                 # no GPU or network needed
uv run flosub --help
uv run flosub transcribe some-clip.mp3 --format srt
```

`uv` creates `engine/.venv` with Python 3.11, whatever Python your system has. Models download to your per-user data folder (`flosub models list` shows where).

### Blender add-on (`blender_addon/`)

The add-on finds `flosub` on your PATH, so install the engine as a tool first: `uv tool install --editable "./engine[cuda]"` (drop `[cuda]` without an NVIDIA GPU).

```bash
# pure-Python tests (no Blender needed)
uvx pytest blender_addon/tests

# build the extension zip, then install it: Edit → Preferences → Get Extensions → ⌄ → Install from Disk
mkdir -p dist && blender --command extension build --source-dir blender_addon/legendaria --output-dir dist

# tests inside Blender (run with every Blender version you can; CI uses 4.2 LTS and the latest)
blender -b --factory-startup --python-exit-code 1 --python blender_addon/tests/blender_smoke.py -- --media some-clip.mp3 [--real]

# scripted GUI session with screenshots (see the script's docstring)
xvfb-run -a -s "-screen 0 1600x900x24" blender --python blender_addon/tests/ui_walkthrough.py -- --media some-clip.mp3 --out shots/
```

Every user-visible string must be in `blender_addon/legendaria/locales/pt_BR.json`; `python3 blender_addon/tests/test_i18n.py pt_BR` lists what is missing. API differences between Blender versions go in `compat.py` only.

### Keeping `docs/PROJECT.md` in sync

`python3 tools/project_map.py <files...>` prints the file map entries (line counts, functions, docstrings). Paste them into `docs/PROJECT.md`, section 6.

## Workflow

1. **Branch from `main`:** `feat/<topic>`, `fix/<topic>` or `docs/<topic>`. `main` is protected and only changes through pull requests.
2. **Commit** with [Conventional Commits](https://www.conventionalcommits.org/): `feat: add VTT export`, `fix(engine): handle silent audio`, `docs: ...`, `refactor: ...`, `test: ...`, `chore: ...`.
3. **Keep the docs in sync**, in the same PR (see [`docs/dev-docs/README.md`](docs/dev-docs/README.md)):
   - Add a devlog step in `docs/dev-docs/devlog/`.
   - Update `docs/PROJECT.md`: files, functions, line counts.
   - Write a plan or an ADR when the change needs one.
   - Add user-visible changes to `CHANGELOG.md` under "Unreleased".
4. **Open a pull request.** CI runs lint and tests on Linux, macOS and Windows, and must pass. PRs are squash-merged, so the PR title becomes the commit message on `main`; give it a Conventional Commits title.

## Releasing (maintainers)

1. Bump `version` in `engine/pyproject.toml` and `engine/legendaria_engine/__init__.py`, and move the "Unreleased" entries of `CHANGELOG.md` under the new version. Merge that through a PR.
2. Tag `main` and push the tag: `git tag v0.2.0 && git push origin v0.2.0`.
3. The `Release` workflow checks that the tag matches the version, runs the tests, builds, and publishes to [PyPI](https://pypi.org/project/legendaria/) through Trusted Publishing (no tokens).
4. Create a GitHub Release from the tag, with the changelog notes.

## Code style

- Python is formatted and linted by [ruff](https://docs.astral.sh/ruff/) (config in `ruff.toml`). `pre-commit` runs it for you.
- Cross-platform always: use `pathlib`, pass `subprocess` an argument list (never `shell=True`), and hardcode no OS-specific paths.
- Behavior that users may want to tweak belongs in JSON config files, not in code.
- No user-visible string in code without going through the translation layer.

## Adding a language

English is the source language and Brazilian Portuguese (`pt_BR`) is always maintained. To add or fix a language:

- **README:** copy `README.md` to `README.<lang>.md`, translate it, and add a link in the language line at the top of every README.
- **Blender add-on:** add `blender_addon/legendaria/locales/<lang>.json` (format described in `locales/README.md`, once the add-on exists).
- **Brand taglines:** add an entry to `TAGLINES` in `assets/brand/source/generate_hero.py`.

Open a [translation issue](https://github.com/flou-ainan/Legendaria/issues/new?template=translation.yml) if you want to coordinate first.

## Licensing

By contributing, you agree that your contribution is licensed under the license of the folder you change:

- **MIT** for the engine and the rest of the repository;
- **GPL-3.0-or-later** for `blender_addon/`.

See [ADR-004](docs/dev-docs/decisions/ADR-004-dual-licensing.md).

## Conduct

Everyone taking part follows our [Code of Conduct](CODE_OF_CONDUCT.md).
