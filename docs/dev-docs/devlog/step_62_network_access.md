# Step 62 — Network access: password, gate, launcher (plan 12, ADR-026)

**Date:** 2026-11-02
**Agent/author:** Claude Code (Sonnet 5.5)
**Related plan:** planning/plan_12_network_access_and_login.md
**Commit(s):** on branch `feat/network-access` (see `git log`)

## What was done

- **`access.py`** (no HTTP): `access.json` (scrypt hash, session secret, switches `lan`, `require_password_here`, `allow_public`, mode 0600), signed 30-day session tokens, a rate limiter (per address and global), password checks and a generator (`xxxx-xxxx-xxxx`), the local/remote test, the private-peer test, the `Host` allowlist.
- **`server.py`:** one deny-by-default gate before any route. No password: listens on 127.0.0.1 only. Password: listens on the network. A request from a browser on this computer needs nothing; anything else needs the `legendaria_auth` cookie. A signed-in remote client may browse and open the computer's files; `remote_browse: false` turns that into 403 on `/api/browse` and `/api/open` (changed the same day: the first version blocked it, against the owner's wish). New routes: `/api/access`, `/api/login`, `/api/logout`, `/api/access/password`. `nosniff` and `no-referrer` headers. API version 6.
- **CLI:** `flosub auth status|set|reset` (and `--generate`); `flosub serve` offers to set the password when it is missing (terminal only, `--no-prompt` to skip). `--allow-host` names are remote and need the password.
- **i18n for the engine:** `i18n.py` and `locales/en.json`, `locales/pt-BR.json` for the terminal prompts and the launcher.
- **Web:** `SignIn.svelte`, `Access.svelte` (addresses, change or generate the password, sign out), "Access and password…" in the File menu, `ApiError` with codes, texts in en and pt-BR.
- **Launcher:** `launcher.py` (tkinter) and the `legendaria` gui script: splash, first-run password dialog (asked every time until one is set, "Not now" starts local-only), the (i) balloon with a link to the guide, restart on the network when the password is set while running. Falls back to the terminal without tkinter or a display.
- **Docs:** `docs/network-access.md` and `.pt-BR.md`, README summaries, SECURITY scope, CHANGELOG, ADR-026 and plan 12 synced with the code, PROJECT.md.
- **CI:** the engine tests run on a virtual display on Linux, so the launcher window tests run.

## Why

The owner wants the phone to reach the editor with no manual setup, with a password for every non-local access because the Wi-Fi is shared with visitors (ADR-026).

## Files touched

`engine/legendaria_engine/{access,access_prompt,i18n,launcher,server,cli}.py`, `engine/legendaria_engine/locales/`, `engine/pyproject.toml`, `engine/tests/test_{access,access_prompt,server_access,launcher,server}.py`, `web/src/` (App, Menu, SignIn, Access, api, password, locales), `web/e2e/smoke.mjs`, `.github/workflows/ci.yml`, docs.

## How it was tested

- Engine: the whole suite passes; `test_server_access.py` walks every `/api/...` route (found by scanning `server.py`) as an anonymous remote client. The gate was also broken on purpose four ways (any cookie accepted, remote may browse, proxy headers ignored, no fail-closed) and the tests caught each one.
- Launcher: the window tests (first run, "Not now", bad password, generate, change while running, the (i) link) pass on a virtual display (`xvfb-run`); they skip without a display.
- Web: `svelte-check`, Vitest, and the Playwright smoke test, which now also signs in from a "phone" (a second server with a password, reached by another name), browses the computer's files, and signs out.
- Looked at the launcher and the password dialog in a screenshot (pt-BR).
- **Not tested:** a real phone, a real Tailscale or Headscale network (only the headers `tailscale serve` adds are simulated), the launcher on Windows and macOS, the firewall steps in the guide.

## Pending / next steps

The owner tests it by hand. Step 7 of plan 12 (optional HTTPS, stricter CSP, upload quota) is parked.
