# Agent instructions

Applies to every agent (Claude Code, Gemini/Antigravity, OpenCode, Copilot, Codex, ...).

## Before you start

1. Read `docs/PROJECT.md`: overview, stack, decisions, and a file map with line counts and functions.
2. Read the latest step in `docs/dev-docs/devlog/` and any open plan in `docs/dev-docs/planning/` to see what is in progress.
3. Only then open the source files related to the task. Do not scan the whole repository when the docs already answer the question.

## Documentation rules (mandatory)

Full conventions: `docs/dev-docs/README.md`. Summary:

- **Every plan becomes a file** in `docs/dev-docs/planning/` before implementation starts.
- **Every change is logged** as a step in `docs/dev-docs/devlog/`: what changed, why, files touched, how it was tested.
- **Every relevant technical decision** (library, architecture, format) becomes an ADR in `docs/dev-docs/decisions/`.
- **`docs/PROJECT.md` always reflects the current code.** Any change to files, functions, stack, or folder layout updates `PROJECT.md` in the same commit, including line counts. Generate the file map entries with `python3 tools/project_map.py <files>`; give every public function a one-line docstring so the map stays useful.

Goal: someone who clones the repository, with no access to any agent memory, can understand the project and what is going on just by reading `docs/`.

## Language policy

- **English** for everything developer-facing: dev docs, `PROJECT.md`, plans, devlogs, ADRs, code, identifiers, comments, commit messages, folder names.
- **User-facing content is translatable** with English as the source: README (`README.md` + `README.pt-BR.md`), user docs, and the Blender UI (locale files). Brazilian Portuguese (`pt_BR`) is always maintained; other languages are welcome from contributors.
- Never hardcode a user-visible string in code without routing it through the translation layer.

## Engineering principles

- **Cross-platform from day one:** Linux, macOS, Windows 10+. Use `pathlib`, never shell strings, no OS-specific paths in code.
- **Hackable:** behavior that a user might want to tweak lives in JSON config files, not in code.
- **Friendly to users and contributors:** clear errors, sensible defaults, no manual environment setup.

## Cross-agent memory

This machine uses [ai-memory](https://github.com/akitaonrails/ai-memory) to carry context between agents. It is a complement: the source of truth for project state is always `docs/`.

## Branches and commits

`main` is protected: work on a branch, commit with Conventional Commits, open a PR, and wait for the `ci` check (ADR-008).

## General

- Never commit secrets, API keys, media test files, or files listed as local-only in `.gitignore`.
- Preserve local changes that are not yours.
- When done, report what was validated.
