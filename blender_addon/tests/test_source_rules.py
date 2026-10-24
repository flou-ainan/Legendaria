"""Static checks for Blender API pitfalls that only show up when a dialog actually opens."""

import ast
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1] / "legendaria"
# WindowManager.invoke_confirm(icon=...) accepts only these (Blender 4.2 and 5.x).
CONFIRM_ICONS = {"NONE", "WARNING", "QUESTION", "ERROR", "INFO"}


def test_invoke_confirm_icons_are_allowed():
    bad = []
    for path in ADDON.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "invoke_confirm":
                bad += [
                    f"{path.name}:{node.lineno} icon={kw.value.value}"
                    for kw in node.keywords
                    if kw.arg == "icon"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value not in CONFIRM_ICONS
                ]
    assert not bad, bad
