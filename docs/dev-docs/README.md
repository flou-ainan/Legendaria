# Development documentation conventions

The whole history of the project lives as markdown inside the repository. This is a contingency: even without ai-memory or any agent memory, anyone who clones the project can see what exists, what was done, and what is in progress.

All files here are written in **English**.

## Layout

```
docs/
├── PROJECT.md              # project map, always up to date
└── dev-docs/
    ├── README.md           # this file
    ├── planning/           # plans, written before implementing
    ├── devlog/             # one step per change or executed stage
    ├── decisions/          # ADRs: technical decisions and their reasons
    └── references/         # background material (e.g. the origin brainstorm)
```

## `docs/PROJECT.md`

A condensed file that helps agents and people find what they need fast, without rereading the code. It contains:

1. Project overview
2. Chosen architecture
3. Technologies / stack
4. Technical decisions (summary linking to each ADR)
5. Folder structure
6. File map: for every source file, its line count and a short description of each function or class, with the line where it starts

**Rule:** every change to the project updates `PROJECT.md` in the same commit. Count lines with `wc -l`.

## Plans — `planning/plan_NN_<topic>.md`

Written **before** implementing. Sequential numbering (`plan_02_capcut_styles.md`).

```markdown
# Plan NN — <topic>

**Status:** proposed | approved | in progress | done | abandoned
**Date:** YYYY-MM-DD

## Goal
## Context
## Proposed changes   (files to create/change and what changes in each)
## Open questions
## Definition of done / how to test
```

Update the status as it changes.

## Devlog — `devlog/step_NN_<topic>.md`

One file per change or executed stage, sequential numbering (`step_03_engine_cli.md`). It records what **was done**, not what is intended.

```markdown
# Step NN — <topic>

**Date:** YYYY-MM-DD
**Agent/author:** <who>
**Related plan:** planning/plan_NN_<topic>.md (if any)
**Commit(s):** <hash>

## What was done
## Why
## Files touched
## How it was tested
## Pending / next steps
```

## Technical decisions — `decisions/ADR-NNN-<topic>.md`

For choices someone may question later: library, architecture, file format, change of approach.

```markdown
# ADR NNN — <title>

**Status:** proposed | accepted | superseded by ADR-XXX
**Date:** YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Consequences
```

When you create an ADR, add a row to the "Technical decisions" table in `PROJECT.md`.

## Flow of a change

1. Plan → `planning/plan_NN_*.md`
2. If there is a technical decision → `decisions/ADR-NNN-*.md`
3. Implement
4. Log → `devlog/step_NN_*.md`
5. Update `PROJECT.md`
6. Commit code and docs together
