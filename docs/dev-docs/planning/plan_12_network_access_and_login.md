# Plan 12 — Reach the editor from the phone: LAN mode, login, docs

**Status:** open, not started (owner decision 2026-10-28, ADR-024)
**Related:** ADR-024, plan 11, plan 08

## Goal

Using the editor from a phone on the same Wi-Fi works with one flag and no third party; away from home Tailscale is the documented path; and nobody on the network can use the editor without signing in.

## Steps (each useful by itself)

1. **LAN mode.** A flag to listen on all interfaces (e.g. `--host 0.0.0.0`; default stays `127.0.0.1`). Print the URLs to open (`http://<LAN IP>:<port>`), accept that `Host` (private ranges), keep the `--allow-host` list for names. Tests for the host check.
2. **Login.** User name and password set in Legendária (a `flosub auth set` command or a first-run prompt), stored hashed (scrypt from the standard library) in the user config dir, never in the project. Required whenever the server listens beyond `127.0.0.1` (opt-out only on localhost). Sign-in page, session cookie (separate from `legendaria_client`, `HttpOnly`, `SameSite=Strict`), rate limit on failures, constant-time compare. Needs its own threat-model notes in the ADR before code (security-sensitive).
3. **Docs.** README (+ pt-BR) section "Use it from your phone": LAN first, Tailscale for outside (install, `tailscale serve --bg <port>`, one-time `tailscale set --operator`), tunnels as an aside. Mention the Headscale alternative.
4. **Later, after the MVP (owner):** reorganize and slim the project, and ship an end-user installer ("next > next"). Out of this plan; get its own plan then.

## Not in scope

Accounts with several users and roles, password reset by email, TLS inside Legendária (use Tailscale or a reverse proxy), the paid-version server.

**Next task:** step 1 (LAN mode) — tier: standard, effort: medium — small server change with a clear pattern; step 2 (login) — tier: top, effort: medium — security-sensitive.
