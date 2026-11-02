# Translating the interface

Each language is **one JSON file** in this folder. There is no code to change: the app finds every `*.json` here and lists it in the menu (File ▸ Language).

1. Copy `en.json` to a new file named with the language code: `es.json`, `fr.json`, `pt-PT.json`, `zh-CN.json`…
2. Set `"_name"` to the language's name **in that language** (it is what the menu shows), then translate the values. Keep the keys (left side) as they are.
3. Keep `{placeholders}` such as `{name}` or `{pct}` exactly as written; move them where the sentence needs them.
4. Missing keys are fine: the app falls back to English for them. Run `npm test` in `web/` to see which keys are missing or misspelled.
5. Open a pull request with the file. If you cannot use git, send the file to the maintainers in an issue.

`pt-BR.json` is always kept complete (a test enforces it). The browser's language picks the default; the menu choice is remembered.
