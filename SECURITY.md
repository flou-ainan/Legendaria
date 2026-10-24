# Security policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report them privately through GitHub: [**Report a vulnerability**](https://github.com/flou-ainan/Legendaria/security/advisories/new) (the **Security** tab of this repository). You can write in English or Portuguese.

Please include what is affected, how to reproduce it, and its impact if you know it. You will get an answer as soon as possible; this is a volunteer project, so allow a few days.

## Supported versions

Until 1.0, only the latest release gets security fixes.

## Scope

Legendária runs locally and needs no account. The areas most relevant to security:

- the engine installer: it downloads `uv`, Python packages and Whisper models;
- the way the Blender add-on launches the engine process;
- the parsing of config, transcript and media files.
