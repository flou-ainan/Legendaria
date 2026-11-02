# ADR 026 — Network access: LAN by default, a password for every non-local access, a light launcher

**Status:** accepted (owner, 2026-11-02)
**Date:** 2026-11-02
**Related:** ADR-024 (partly superseded: LAN becomes the default, with a password), ADR-023, plan 12

## Context

The owner's requirements (2026-11-02): ease of use, hackable, modular and robust are the core principles. The phone is another screen for the editor, so reaching it over the local network should work by default. A guest on the home Wi-Fi, who does not know the password, must not be able to read the computer's files ("Wi-Fi is shared with visitors; the files of the main computer are not"). The password is set the first time the user runs the app, is the same for LAN, Tailscale and Headscale, and lives in a Legendária settings JSON. A small tkinter launcher opens the app.

What the server exposes today, which is what a password has to protect: a file browser over the whole disk (`/api/browse`), opening any path (`/api/open`), media streaming, the glossary, transcription and FFmpeg export jobs. It binds `127.0.0.1` and checks `Host` and `Origin`.

## Threat model

| Who | Wants | Seen as |
|---|---|---|
| A guest on the same Wi-Fi | read or delete files, burn CPU, see projects | the main threat |
| A web page open in the owner's browser | reach the local server (CSRF, DNS rebinding) | already covered by the `Host` and `Origin` checks; kept |
| Someone capturing the LAN traffic | take the password or the session | real on plain HTTP; see "Transport" below |
| The internet (port forward, tunnel) | the same as the guest | must need the password and must not be reachable by accident |
| Another user or process on the same computer | anything | out of scope: they can read the user's files anyway |

## Decision

1. **Fail closed on binding.** No password set: the server listens on `127.0.0.1` only. A password set: it listens on all interfaces (LAN is the default). `access.json` has `lan: false` to stay local-only. There is no flag to listen beyond localhost without a password.
2. **What counts as "this computer".** A request is local only if the peer address is loopback, `Host` is a loopback name, and no proxy header is present (`Forwarded`, `X-Forwarded-*`, `Tailscale-*`, `CF-*`). Tunnels and `tailscale serve` connect from loopback, so the header rule is what makes them count as remote. Local requests need no password (the launcher opens the browser on this computer); `access.json` `require_password_here: true` turns that off. Everything else needs the password: LAN, Tailscale, Headscale, tunnels.
3. **Refuse public addresses.** A peer that is not loopback, private (RFC 1918), link-local, unique-local or CGNAT (Tailscale's `100.64.0.0/10`) is refused, even with the right password, unless `allow_public: true` is set. This blocks an accidental port forward.
4. **The password is the key to the files.** A signed-in remote client may browse the computer's folders and open its videos, as the owner on their phone (owner, 2026-11-02: "after the password I want to open the computer's files from the phone"). What it cannot do without the password is anything at all. `access.json` has `remote_browse: false` for someone who wants other devices limited to uploading a video from the device and downloading their own exports; the server enforces it, not only the UI. The listing shows folders and media or project files only, and a file is only streamed once it has been opened as a video.
5. **Deny by default, in one place.** One gate runs before any routing. For a remote client, only the app's static files (the sign-in screen is part of the app), `/api/login`, `/api/logout` and `/api/access` (status) pass without a session. With no password set, a remote request gets nothing at all. A new route is protected without anyone remembering to protect it. A test walks every route as an anonymous remote client and expects 401.
6. **Password storage.** `access.json` in the user config dir (its own file, so `config.json` can be pasted into a bug report without leaking anything), mode `0600` where the OS has it. It holds a scrypt hash (`n=2**15, r=8, p=1`, 16-byte salt, parameters stored with it so they can be raised later), a random session secret, and the switches above. The password itself is never stored, logged or sent back.
7. **Setting it must be easy.** A minimum of 8 characters and a short denylist of the most common ones, plus a "Generate for me" button that makes a random `xxxx-xxxx-xxxx` (12 symbols from a 32-symbol alphabet, 60 bits, easy to type on a phone). The same dialog appears in the launcher and, in a terminal, in `flosub serve` and `flosub auth set`. If no password is set, it is offered on every start until it is (the owner's rule); "Not now" starts local-only.
8. **Sessions.** The session cookie is `HttpOnly`, `SameSite=Strict`, `Max-Age` 30 days, and `Secure` when the request came over HTTPS. Its value is an expiry and a nonce signed with the session secret (HMAC-SHA256), so sessions survive a restart and need no server state. Changing the password rotates the secret and signs everyone out.
9. **Brute force.** Per client address: after 5 consecutive failures the delay doubles each time, up to 15 minutes; plus a global cap so many addresses cannot add up. Comparison is constant time (`hmac.compare_digest`), the answer is the same for every failure, and failures are printed in the terminal.
10. **`Host` allowlist.** Loopback names, any private IP literal (someone typed an address, which is not DNS rebinding), this computer's host name and `<host name>.local`, plus `--allow-host` for Tailscale or Headscale names. Any other name is refused, which keeps DNS rebinding blocked. `Origin`, when present, must be the same host as `Host`.
11. **Small headers.** Add `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer` to the existing isolation headers. A strict `Content-Security-Policy` is later (JASSUB's workers and WASM need care).
12. **Modules.** `access.py` holds the settings file, hashing, tokens, rate limit and the local/remote test, with no HTTP in it. `server.py` only calls it. `launcher.py` holds the tkinter window and imports nothing from the server except a start function. User-visible texts go through the locale files (en, pt-BR).

### Transport (the honest limit)

On the LAN the editor speaks plain HTTP, so the password and the session cookie cross the Wi-Fi unencrypted. That keeps casual guests out, but it does not stop someone who can capture traffic on the same network (for example a guest on a shared WPA2 key). What we do about it:

- The docs say it plainly and recommend a guest Wi-Fi with client isolation, or Tailscale / Headscale, which encrypt the traffic (WireGuard) and give HTTPS through `tailscale serve`.
- A later step adds an optional HTTPS mode with a self-signed certificate whose fingerprint the launcher shows. It needs a certificate library or OpenSSL, so it is not in the first slice.

## Alternatives considered

- **Only Tailscale:** ties the product to a third-party service and to an account. Kept as the recommended way away from home.
- **A token in the URL or a QR code (as Jupyter does):** very practical on a phone, but the token sits in history and referrers, and the owner asked for a password. May return later as a convenience on top of the password.
- **A password-authenticated key exchange (SRP) to avoid sending the password:** not in the standard library and easy to get wrong; TLS is the right fix for this problem.
- **Password for this computer too:** safer on a shared computer, annoying for the common case. Available as a switch, off by default.
- **Several users and roles:** not needed for a personal tool.

## Consequences

- LAN mode and the password ship together, in the same release. The server never listens beyond loopback without one.
- `--allow-host` stops being a bare switch: a request through that name is remote and needs the password.
- A signed-in phone can open videos from the computer's disk as well as upload its own; with `remote_browse: false` it can only upload. Whoever has the password can see the folder names the editor's user can see, so the password is as sensitive as the account.
- The launcher needs tkinter. If it is missing (some Linux packages split it out), the app falls back to the terminal prompt and says how to install it.
- Brute-force limits and `access.json` become behaviour that tests must pin down.
