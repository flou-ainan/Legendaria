# Step 00 — Repository and documentation setup

**Date:** 2026-10-23
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan
**Commit(s):** c093ebc, a3d16d4

## What was done

1. Created the git repository on `main` with `README.md`, `.gitignore` (Python, Node, `.env`, media files) and `LICENSE` (MIT).
2. Created the public GitHub repository: https://github.com/flou-ainan/Open-Subtitler
3. Created the documentation structure: `AGENTS.md`, `CLAUDE.md` (points to `AGENTS.md`), the project map and `docs/dev-docs/` with plans, devlog and decisions.
4. Installed [ai-memory](https://github.com/akitaonrails/ai-memory) v3.2.2 on the development machine and connected it to Claude Code, OpenCode, Antigravity CLI and Copilot CLI.

## Why

The project will be built by switching between different AI agents, so there is a double contingency:

- **ai-memory:** automatic memory shared across agents and sessions, local to the machine.
- **`docs/` in git:** plans, devlog, ADRs and the project map. Works with no tool at all, for anyone who clones the repository.

The documentation pattern follows the one already used in the author's other projects.

## Files touched

- `README.md`, `.gitignore`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`
- The project map (now `docs/PROJECT.md`), `docs/dev-docs/README.md`, this file

## How it was tested

- `git push` to `origin/main` succeeded.
- `ai-memory setup` finished with `healthz: ok` and `memory_status: ok`.

## Pending / next steps

- Restart the agents so they load the ai-memory hooks.
