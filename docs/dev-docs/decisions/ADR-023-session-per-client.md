# ADR 023 — One server session per browser

**Status:** accepted (owner approved plan 11)
**Date:** 2026-10-28
**Related:** plan 11 (item B), ADR-014 (local server), step 50 (tunnels)

## Context

`flosub serve` kept a single `Session` (the open video, its jobs and cache) for the whole server. With a phone and a computer connected at once, opening a video on one changed what the other saw, and both could overwrite the same project.

## Decision

- The server sets a cookie `legendaria_client` (random id; `HttpOnly`, `SameSite=Strict`, one year) on the first response to a browser without one, and keeps `sessions: dict[id, Session]`.
- A video given on the command line is opened lazily, as a separate `Session`, for each browser that connects.
- `API_VERSION` goes to 5, so a page built for the old server shows the restart banner.

## Alternatives considered

- **An id sent in a header or the URL by the page:** needs code in every request, and `EventSource` and `<video src>` cannot set headers. A cookie reaches all of them with no client code.
- **An id in `localStorage` sent as a query parameter:** works, but every URL carries it and it leaks into logs; the cookie is simpler and not readable by scripts.

## Consequences

- Different browsers (or profiles) never see each other's open video. Tabs of the same browser share one session on purpose (same person, same work).
- Sessions are kept in memory until the server stops; one entry per browser is small. Pruning idle sessions can come later.
- Two browsers that open the same video still write the same project file. A warning or a version check on save is still to do (plan 11, B).
