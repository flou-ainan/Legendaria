"""The fonts bundled with Legendária (open licence), listed in `fonts/fonts.json`."""

from __future__ import annotations

import json
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent / "fonts"


def catalog() -> list[dict[str, object]]:
    """The bundled families: `family`, `file`, `bold` (the file is the bold cut), `category`."""
    return json.loads((FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))


def file_for(family: str) -> Path | None:
    """The bundled font file for `family` (case-insensitive), or None."""
    for entry in catalog():
        if str(entry["family"]).lower() == family.lower():
            return FONTS_DIR / str(entry["file"])
    return None
