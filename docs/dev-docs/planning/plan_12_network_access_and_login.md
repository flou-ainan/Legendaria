# Plan 12 — Network access: LAN with a password, a launcher, and the docs

**Status:** steps 1–6 built (step 62), waiting for the owner's hands-on test; step 7 is later
**Related:** ADR-026 (the design and the threat model), ADR-024 (partly superseded), plan 11, plan 15

## Goal

A user installs Legendária, opens the launcher, sets a password once, and from then on reaches the editor from a phone on the same Wi-Fi without any command line. Nobody without the password can use it, and a guest on the Wi-Fi can never browse the computer's files. Tailscale or Headscale work with the same password.

Core principles for every step: easy to use, hackable (a settings JSON, no hidden state), modular, robust.

## What exists now (step 62)

Steps 1–6 are built: `access.py`, the gate in `server.py`, the web sign-in and Access dialog, `flosub auth`, the `legendaria` launcher and the guide in `docs/network-access.md` (+ pt-BR). Not yet checked: a real phone, a real Tailscale or Headscale network, the launcher on Windows and macOS.

## Steps (each leaves the app working)

1. **`access.py`, the core.** `access.json` in the config dir (mode 0600): scrypt hash, session secret, switches (`lan`, `require_password_here`, `allow_public`). Hash and verify, make and check signed session tokens, per-address rate limit, the local/remote test, the peer-address filter, the password generator. No HTTP. Unit tests, including timing-safe compare, rotation on password change, and header-based remote detection.
2. **Server enforcement.** One deny-by-default gate before routing. `/api/login`, `/api/logout`, `/api/access` (status). Remote clients lose `/api/browse` and open-by-path. LAN binding when a password is set, `Host` allowlist with the machine's addresses and names, small headers. A test that walks every route as an anonymous remote client and expects 401, and one that checks the remote restrictions. Security-sensitive: review it twice.
3. **Web.** A sign-in screen, an "Access" item in the File menu (change password, sign out, show the addresses to open on the phone), a clear message when the session ends. Texts in `en.json` and `pt-BR.json`. The existing `remote` mode keeps working.
4. **CLI.** `flosub auth set | reset | status`; `flosub serve` offers to set the password when it is missing (on a terminal, with hidden input), prints the LAN address when it is on, and keeps `--allow-host` for Tailscale and Headscale.
5. **Launcher (tkinter).** Entry point `legendaria`. A splash window while the server starts, then it opens the browser. First run, and every run until a password is set: a dialog to set it, with "Generate for me" and "Not now" (starts local-only). An (i) balloon explains what LAN access is for and links to the network doc (the language of the launcher picks the pt-BR or en file). MVP has one option, "Open app". Fallback to the terminal prompt when tkinter is missing. Its texts are locale files.
6. **Docs.** `docs/network-access.md` and `docs/network-access.pt-BR.md`: what LAN access is, the password, plain-HTTP limits and the guest Wi-Fi advice, Tailscale and Headscale (install, `tailscale serve`, `--allow-host`), why never to open a router port. README and README.pt-BR get a short summary with a link. The launcher's (i) links to this file.
7. **Later (not in the first slice):** optional HTTPS with a self-signed certificate and its fingerprint, a pairing QR code, a stricter `Content-Security-Policy`, an upload quota for remote clients, a larger password denylist.

## Not in scope

Accounts with several users and roles, password reset by email, TLS terminated by Legendária in the first slice, the paid-version server.

## Definition of done

- With no password the server listens only on `127.0.0.1` (tested).
- With a password, an anonymous request from another address gets 401 on every route (tested), a wrong password is throttled, and a signed-in phone cannot list the computer's folders.
- The whole flow works from the launcher on Linux; Windows and macOS are checked in CI where possible and by the owner otherwise.
- `PROJECT.md`, the devlog and the READMEs match the code.

**Next task:** the owner tests it by hand (phone on the Wi-Fi, then Tailscale) and sends corrections — tier: standard, effort: medium — fixes against a written design. Step 7 (optional HTTPS, stricter CSP, upload quota) — tier: top, effort: medium — security-sensitive.
