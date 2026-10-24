# SPDX-License-Identifier: GPL-3.0-or-later
"""UI translations (ADR-005): English source strings, `locales/<lang>.json` dictionaries.

Each locale file maps English text to its translation. Strings are registered in the
default and the operator contexts, so labels, buttons and tooltips are all covered.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
CONTEXTS = ("*", "Operator")


def load_translations() -> dict[str, dict[tuple[str, str], str]]:
    """{blender_locale: {(context, english): translated}} from every locales/*.json."""
    table: dict[str, dict[tuple[str, str], str]] = {}
    for path in sorted(LOCALES_DIR.glob("*.json")):
        entries = json.loads(path.read_text(encoding="utf-8"))
        entries.pop("$comment", None)
        table[path.stem] = {(ctx, src): dst for src, dst in entries.items() for ctx in CONTEXTS}
    return table


def tr(text: str) -> str:
    """Translate a dynamic UI string (reports, formatted messages) for the current locale."""
    return bpy.app.translations.pgettext_iface(text)


def register(package: str) -> None:
    """Register the dictionaries under the add-on's package name."""
    bpy.app.translations.register(package, load_translations())


def unregister(package: str) -> None:
    """Remove the dictionaries."""
    bpy.app.translations.unregister(package)
