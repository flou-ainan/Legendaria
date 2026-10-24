"""Every user-visible string in the add-on must have a translation in each locale file.

Run directly to list what is missing: python3 blender_addon/tests/test_i18n.py pt_BR
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ADDON = Path(__file__).resolve().parents[1] / "legendaria"
UI_KEYWORDS = {"text", "name", "description", "title", "message", "confirm_text"}
NOT_UI = {"legendaria.refresh_engine"}  # operator ids passed positionally are not text


def _strings_in_tuples(node: ast.AST) -> list[str]:
    """Labels and descriptions of enum items: (id, label, description) tuples."""
    out = []
    for tup in ast.walk(node):
        if isinstance(tup, ast.Tuple) and len(tup.elts) >= 3:
            out += [
                e.value
                for e in tup.elts[1:3]
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            ]
    return out


def ui_strings() -> set[str]:
    """Collect UI text from the add-on source."""
    found: set[str] = set()
    for path in ADDON.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "tr" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.add(arg.value)
                for kw in node.keywords:
                    if (
                        kw.arg in UI_KEYWORDS
                        and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)
                    ):
                        found.add(kw.value.value)
                    if kw.arg == "items" and not isinstance(kw.value, ast.Name):
                        found.update(_strings_in_tuples(kw.value))
            elif isinstance(node, ast.ClassDef):
                is_operator = any(
                    getattr(b, "attr", getattr(b, "id", "")) == "Operator" for b in node.bases
                )
                if is_operator and ast.get_docstring(node):
                    found.add(ast.get_docstring(node))
                for stmt in node.body:
                    if (
                        isinstance(stmt, ast.Assign)
                        and any(getattr(t, "id", "") == "bl_label" for t in stmt.targets)
                        and isinstance(stmt.value, ast.Constant)
                    ):
                        found.add(stmt.value.value)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = {getattr(t, "id", "") for t in targets}
                if names & {"LANGUAGE_ITEMS", "STYLE_ITEMS"}:
                    found.update(_strings_in_tuples(node.value))
                if names & {"LANGUAGE_NAMES", "STYLE_LABELS"} and isinstance(node.value, ast.Dict):
                    for value in node.value.values:
                        if isinstance(value, ast.Constant):
                            found.add(value.value)
                        elif isinstance(value, ast.Tuple):
                            found.update(e.value for e in value.elts if isinstance(e, ast.Constant))
    return {s for s in found if s.strip() and s not in NOT_UI and s != "Legendária"}


def locale_files() -> list[Path]:
    return sorted((ADDON / "locales").glob("*.json"))


@pytest.mark.parametrize("path", locale_files(), ids=lambda p: p.stem)
def test_every_ui_string_is_translated(path):
    table = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(ui_strings() - set(table))
    assert not missing, f"{path.name} is missing {len(missing)} strings: {missing}"


@pytest.mark.parametrize("path", locale_files(), ids=lambda p: p.stem)
def test_placeholders_match(path):
    import re

    table = json.loads(path.read_text(encoding="utf-8"))
    table.pop("$comment", None)
    for source, translated in table.items():
        assert set(re.findall(r"\{\w+\}", source)) == set(re.findall(r"\{\w+\}", translated)), (
            source
        )


def test_pt_br_exists():
    assert (ADDON / "locales" / "pt_BR.json").is_file()


if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else "pt_BR"
    path = ADDON / "locales" / f"{lang}.json"
    have = set(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else set()
    for s in sorted(ui_strings() - have):
        print(json.dumps(s, ensure_ascii=False))
