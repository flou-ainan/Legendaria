# Step 61 — Network access design: password, launcher, threat model

**Date:** 2026-11-02
**Agent/author:** Claude Code (Sonnet 5.5)
**Related plan:** planning/plan_12_network_access_and_login.md
**Commit(s):** see `git log` (docs only)

## What was done

- ADR-026: threat model and decisions for network access. LAN is the default once a password is set; no password means localhost only; the password covers every non-local access (LAN, Tailscale, Headscale, tunnels); remote clients cannot browse the computer's disk; deny-by-default gate; scrypt in `access.json`; signed stateless sessions; rate limit; public addresses refused. ADR-024 marked as partly superseded.
- Plan 12 rewritten into seven steps (core, server gate, web, CLI, tkinter launcher, docs en + pt-BR, later hardening).
- `ROADMAP.md`, plan 15, `chat-context.md` and the ADR table in `PROJECT.md` updated.

## Why

The owner asked for a safe and easy way to reach the editor from a phone, with a first-run password, a light launcher and bilingual docs. The Wi-Fi is shared with guests, so the password must apply to every non-local access, and the file browser must not be reachable remotely.

## Files touched

`docs/dev-docs/decisions/ADR-026-*`, `ADR-024-*`, `planning/plan_12_*`, `planning/plan_15_*`, `ROADMAP.md`, `chat-context.md`, `docs/PROJECT.md`.

## How it was tested

Nothing in the code changed. The design relies on what was read in `server.py` (routes, `Host` and `Origin` check) and on the step 60 check that the live preview renders on plain HTTP in desktop Chromium. Not measured: a real phone, and playback speed over Wi-Fi.

## Pending / next steps

Plan 12, step 1. The tkinter launcher is untested on Windows and macOS.
