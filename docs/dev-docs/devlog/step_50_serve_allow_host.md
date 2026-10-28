# Step 50 — `flosub serve --allow-host`, for testing on a phone through a tunnel

**Date:** 2026-10-27
**Related:** step 31 (local-only guard), ADR-017 (file browser)

- The server rejects any request whose `Host` or `Origin` is not `127.0.0.1`/`localhost` (403), so an ngrok URL could not load the editor.
- New opt-in `flosub serve --allow-host HOST` (repeatable) adds extra accepted names. Default unchanged: still local only. The server still binds `127.0.0.1`; the tunnel runs on the same machine.
- **Security note:** the editor has a file browser and can read videos from the disk. Never open a tunnel without protection. With ngrok use `--basic-auth user:password`.
- Recipe: `ngrok http 8767 --basic-auth user:pass`, copy the domain, then `flosub serve --port 8767 --allow-host <domain>`. The free domain changes on every ngrok run.
- Tests: `test_allow_host_opens_only_the_named_host` (403 by default, 200 for the named host, 403 for a foreign Origin). 137 pytest.
- Files: `server.py`, `cli.py`, `tests/test_server.py`.
