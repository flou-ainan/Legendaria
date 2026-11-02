# ADR 024 — How the phone reaches the editor: LAN by default, Tailscale recommended, own login

**Status:** accepted (owner, 2026-10-28); **partly superseded by [ADR-026](ADR-026-network-access-password-and-launcher.md)** (2026-11-02): LAN becomes the default, but only once a password is set; the password applies to every non-local access, tunnels and Tailscale included
**Date:** 2026-10-28
**Related:** plan 12, plan 11, ADR-023, step 50 (tunnels)

## Context

The editor runs on the user's computer and the phone is another screen for it. Tunnels through a third party (ngrok) hit bandwidth limits and need an account. The server listens on `127.0.0.1` only and accepts only known `Host` names. We want the easiest path that needs no third party, and a recommended path for use away from home.

## Decision

- **Default: the local network (LAN).** An opt-in `--host 0.0.0.0` (name to be fixed in plan 12) makes `flosub serve` reachable from the same Wi-Fi. No account, no third party, any OS. It is plain HTTP (no PWA install, editing works).
- **Recommended away from home: Tailscale** (private network, HTTPS with `tailscale serve`). Documented, never required: the editor works alone, on LAN, or through any tunnel. Headscale is mentioned as the self-hosted alternative, not integrated.
- **Own sign-in:** a user name and password configured in Legendária itself, required when the server listens beyond `127.0.0.1`. Details in plan 12.
- Not supported as a recommendation: opening a router port to the internet, bare WireGuard.

## Alternatives considered

- **Headscale as the official option:** open source, but the server needs a public address and HTTPS and is configured by command line; too much for the end user.
- **Open port + dynamic DNS:** exposes the computer to the internet and fails behind CGNAT.
- **Tailscale only:** depends on a company's coordination service; fine as a recommendation, not as the only way.

## Consequences

- A LAN-visible server must not be open to anyone on the network: the sign-in lands before or together with the LAN mode.
- The README gets a short "use it from your phone" section: LAN first, Tailscale for outside.
