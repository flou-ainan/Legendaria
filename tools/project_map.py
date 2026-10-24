"""Print the "File map" entries of docs/PROJECT.md for Python files.

Usage: python3 tools/project_map.py engine/legendaria_engine/*.py

For each file it prints the line count, the module docstring and a table with every
top-level function, class and method: name, signature, line and the first line of
its docstring. Paste the output into PROJECT.md and complete it by hand where useful.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def first_line(node: ast.AST) -> str:
    """First line of a node's docstring, or ""."""
    doc = (
        ast.get_docstring(node)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        else None
    )
    return doc.strip().splitlines()[0] if doc else ""


def signature(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Compact `name(arg, ...)` without self/cls."""
    args = [a.arg for a in fn.args.posonlyargs + fn.args.args if a.arg not in ("self", "cls")]
    if fn.args.vararg:
        args.append("*" + fn.args.vararg.arg)
    args += [a.arg for a in fn.args.kwonlyargs]
    if fn.args.kwarg:
        args.append("**" + fn.args.kwarg.arg)
    return f"{fn.name}({', '.join(args)})"


def rows(tree: ast.Module) -> list[tuple[str, int, str]]:
    """(name, line, summary) for top-level functions, classes and public methods."""
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((signature(node), node.lineno, first_line(node)))
        elif isinstance(node, ast.ClassDef):
            out.append((f"class {node.name}", node.lineno, first_line(node)))
            for item in node.body:
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and not item.name.startswith("_"):
                    out.append((f"{node.name}.{signature(item)}", item.lineno, first_line(item)))
    return out


def describe(path: Path) -> str:
    """Markdown section for one file."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = len(source.splitlines())
    parts = [
        f"### {path.as_posix()} — {lines} lines",
        first_line(tree) or "_(no module docstring)_",
    ]
    table = rows(tree)
    if table:
        parts.append("\n| Function / class | Line | What it does |\n|---|---|---|")
        parts += [f"| `{name}` | {line} | {doc} |" for name, line, doc in table]
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    """Print the sections for the given paths."""
    if not argv:
        print(__doc__)
        return 1
    print("\n".join(describe(Path(p)) for p in argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
