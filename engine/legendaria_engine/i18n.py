"""Texts the engine shows to people (terminal prompts, the launcher), one JSON file per language.

English is the source. A language is a file in `locales/` named by its code (`en.json`,
`pt-BR.json`); drop a new one there and it is found. Missing keys fall back to English.
`LEGENDARIA_LANG` overrides the language, otherwise the system's is used.
"""

from __future__ import annotations

import json
import locale
import os
from functools import cache
from pathlib import Path
from typing import Any

LOCALES_DIR = Path(__file__).parent / "locales"
SOURCE = "en"


@cache
def _load(code: str) -> dict[str, str]:
    try:
        return json.loads((LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def available() -> list[str]:
    """The language codes that have a file."""
    return sorted(p.stem for p in LOCALES_DIR.glob("*.json"))


def language(requested: str | None = None) -> str:
    """The language to use: `requested`, `LEGENDARIA_LANG`, or the system's, matched to a file (else English)."""
    wanted = requested or os.environ.get("LEGENDARIA_LANG") or (locale.getlocale()[0] or "")
    wanted = wanted.replace("_", "-").split(".")[0]
    codes = available()
    for code in codes:
        if code.lower() == wanted.lower():
            return code
    base = wanted.split("-")[0].lower()
    for code in codes:  # `pt` or `pt-PT` still gets `pt-BR` when it is the only Portuguese
        if code.split("-")[0].lower() == base and base != SOURCE:
            return code
    return SOURCE


def t(key: str, lang: str | None = None, **values: Any) -> str:
    """The text for `key` in `lang` (default: `language()`), with `{placeholders}` filled in."""
    code = lang or language()
    text = _load(code).get(key) or _load(SOURCE).get(key) or key
    try:
        return text.format(**values)
    except (KeyError, IndexError):
        return text
