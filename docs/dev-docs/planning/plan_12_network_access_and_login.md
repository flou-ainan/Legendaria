# Plan 12 — Reach the editor from the phone: LAN mode, login, docs

**Status:** open, not started (owner decision 2026-10-28, ADR-024). Its steps are listed in `ROADMAP.md`.
**Related:** ADR-024, plan 11, plan 08

## Goal

Using the editor from a phone on the same Wi-Fi works with one flag and no third party; away from home Tailscale is the documented path; and nobody on the network can use the editor without signing in.

## Steps (each useful by itself)

1. **LAN mode.** A flag to listen on all interfaces (e.g. `--host 0.0.0.0`; default stays `127.0.0.1`). Print the URLs to open (`http://<LAN IP>:<port>`), accept that `Host` (private ranges), keep the `--allow-host` list for names. Tests for the host check.
2. **Login.** User name and password set in Legendária (a `flosub auth set` command or a first-run prompt), stored hashed (scrypt from the standard library) in the user config dir, never in the project. Required whenever the server listens beyond `127.0.0.1` (opt-out only on localhost). Sign-in page, session cookie (separate from `legendaria_client`, `HttpOnly`, `SameSite=Strict`), rate limit on failures, constant-time compare. Needs its own threat-model notes in the ADR before code (security-sensitive).
3. **Docs.** README (+ pt-BR) section "Use it from your phone": LAN first, Tailscale for outside (install, `tailscale serve --bg <port>`, one-time `tailscale set --operator`), tunnels as an aside. Mention the Headscale alternative.
4. **Later, after the MVP (owner):** reorganize and slim the project, and ship an end-user installer ("next > next"). Out of this plan; get its own plan then.

## Open points (2026-10-31, to close with the owner)

What exists today:

- `flosub serve` always binds `127.0.0.1`; there is no `--host` and no login.
- Tailscale already works with no code: `tailscale serve` proxies to the local port, and `--allow-host <machine>.<tailnet>.ts.net` accepts its `Host`. It is not documented for users.

Points to close:

1. **Wording.** ADR-024 says "default: LAN", but the default is and stays `127.0.0.1`. LAN is opt-in; it is the first option for reaching the editor from a phone.
2. **When login is required.** "Listens beyond `127.0.0.1`" misses Tailscale and tunnels, which bind to localhost and proxy to it. Any `--allow-host` opens the editor, including its file browser, to whoever reaches that name. The rule should also cover `--allow-host`, or accept the provider's own access control explicitly (tailnet membership, ngrok `--basic-auth`).
3. **Order.** LAN mode and login ship together (ADR-024). Decide whether they come before or after the owner's corrections.
4. **Plain HTTP limits on LAN.** Checked in desktop Chromium with a local server opened through a non-local name, which makes it an insecure origin: the live subtitle preview still renders, but `isSecureContext` and `crossOriginIsolated` are false, and `SharedArrayBuffer` and `navigator.storage` are missing. So OPFS and the PWA need HTTPS (Tailscale). Not yet measured on a real phone or for playback speed.

## Not in scope

Accounts with several users and roles, password reset by email, TLS inside Legendária (use Tailscale or a reverse proxy), the paid-version server.

**Next task:** step 1 (LAN mode) — tier: standard, effort: medium — small server change with a clear pattern; step 2 (login) — tier: top, effort: medium — security-sensitive.
