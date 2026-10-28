# Agent instructions

Applies to every agent (Claude Code, Gemini/Antigravity, OpenCode, Copilot, Codex, ...).

## Before you start

1. Read `docs/PROJECT.md`: overview, stack, decisions, and a file map with line counts and functions.
2. Read `docs/dev-docs/chat-context.md` (the conversation so far, condensed), the latest step in `docs/dev-docs/devlog/`, and any open plan in `docs/dev-docs/planning/` to see what is in progress.
3. Only then open the source files related to the task. Do not scan the whole repository when the docs already answer the question.

## Documentation rules (mandatory)

Full conventions: `docs/dev-docs/README.md`. Summary:

- **Every plan becomes a file** in `docs/dev-docs/planning/` before implementation starts.
- **Every change is logged** as a step in `docs/dev-docs/devlog/`: what changed, why, files touched, how it was tested.
- **Every relevant technical decision** (library, architecture, format) becomes an ADR in `docs/dev-docs/decisions/`.
- **`docs/PROJECT.md` always reflects the current code.** Any change to files, functions, stack, or folder layout updates `PROJECT.md` in the same commit, including line counts. Generate the file map entries with `python3 tools/project_map.py <files>`; give every public function a one-line docstring so the map stays useful.

- **Conversation hand-off:** keep `docs/dev-docs/chat-context.md` up to date: a lean summary of the whole conversation with the owner, plus your last two complete replies verbatim. Update it when the owner asks and after long stretches of work (hours). It is public, so no secrets or private third-party data. Details: `docs/dev-docs/README.md`.

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

## Recommending the model for the next task

When you finish a task, end your reply to the owner with the model tier and reasoning effort the **next** task needs, and write the same line in the plan's "next" item so it survives a hand-off. The owner prefers **low** or **medium** effort; propose **high** only for a specific reason.

Tiers are vendor-neutral; map them to your own family:

| Tier | Examples (2026) | Use it for |
|---|---|---|
| **standard** | Claude Sonnet, GPT standard / Codex default, Gemini Pro | Work with a written plan and an existing pattern to follow: components, routes, tests, docs, bug fixes with a clear repro, translations. |
| **top** | Claude Opus, GPT top reasoning tier, Gemini top "thinking" tier | New architecture or file formats (ADRs with trade-offs), changes across engine + server + UI at once, opaque debugging (WASM, workers, FFmpeg filter graphs, concurrency), security-sensitive code. |

| Effort | When |
|---|---|
| **low** | Mechanical edits, docs, renames, small fixes. |
| **medium** | The default for feature work. |
| **high** | Only when a wrong design is expensive to undo, or a bug resists a first investigation. Say why. |

Format: `**Next task:** <what> — tier: standard|top, effort: low|medium|high — <one-line reason>`.

## Branches and commits

`main` is protected: work on a branch, commit with Conventional Commits, open a PR, and wait for the `ci` check (ADR-008).

## General

- Never commit secrets, API keys, media test files, or files listed as local-only in `.gitignore`.
- Preserve local changes that are not yours.
- When done, report what was validated.
