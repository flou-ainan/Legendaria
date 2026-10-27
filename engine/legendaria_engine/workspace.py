"""What the web editor needs besides the open video: a file browser, the model and language
lists for the transcribe form, and the glossary library (plan 07).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from legendaria_engine import models, paths
from legendaria_engine.config import read_json, update_user_config
from legendaria_engine.review import glossary

MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v", ".flv", ".wmv", ".mpg", ".mpeg", ".ts",
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac",
}  # fmt: skip


def uploads_dir() -> Path:
    """Where dropped files are stored: `<data dir>/uploads/` (a browser cannot give us the original path)."""
    return paths.data_dir() / "uploads"


def browse(path: str | Path | None = None) -> dict[str, Any]:
    """The folders and media files in `path` (default: the home folder), folders first."""
    target = Path(path).expanduser() if path else Path.home()
    if target.is_file():
        target = target.parent
    target = target.resolve()
    try:
        children = list(target.iterdir())
    except OSError as exc:
        raise ValueError(f"Cannot open {target}: {exc.strerror or exc}") from exc
    entries = []
    for child in children:
        if child.name.startswith("."):
            continue
        try:
            is_dir = child.is_dir()
            if is_dir or child.suffix.lower() in MEDIA_EXTENSIONS:
                entries.append(
                    {
                        "name": child.name,
                        "dir": is_dir,
                        "size": 0 if is_dir else child.stat().st_size,
                    }
                )
        except OSError:
            continue  # broken link or no permission: skip it
    entries.sort(key=lambda e: (not e["dir"], e["name"].lower()))
    parent = None if target.parent == target else str(target.parent)
    return {"path": str(target), "parent": parent, "home": str(Path.home()), "entries": entries}


def languages() -> list[dict[str, str]]:
    """Language codes for the transcribe form: the defaults, or `<config dir>/languages.json` if present."""
    user = paths.config_dir() / "languages.json"
    data = read_json(user if user.is_file() else paths.defaults_dir() / "languages.json")
    return [{"code": code, "name": name} for code, name in data.items()]


def options(config: dict[str, Any]) -> dict[str, Any]:
    """Choices and defaults for the transcribe form."""
    return {
        "models": [
            {k: m[k] for k in ("name", "size_mb", "notes", "installed") if k in m}
            for m in models.list_models()
        ],
        "languages": languages(),
        "styles": sorted(config["styles"]),
        "model": config["model"],
        "language": config["language"],
        "style": config["style"],
    }


def glossary_state() -> dict[str, Any]:
    """The glossary library: names, which one is active, and the active one's text."""
    active = glossary.active_name()
    file = glossary.library_file(active)
    return {
        "active": active,
        "names": sorted({*glossary.list_names(), active}),
        "text": file.read_text(encoding="utf-8") if file.is_file() else "",
    }


def glossary_add(entry: str) -> bool:
    """Add a term or a `wrong -> right` line to the active glossary; False if already there."""
    file = glossary.library_file(glossary.active_name())
    file.parent.mkdir(parents=True, exist_ok=True)
    return glossary.add_entry(file, entry)


def glossary_import(name: str, text: str, activate: bool = True) -> str:
    """Save `text` as the glossary `name` (merging into it when it exists); returns the name."""
    file = glossary.library_file(name)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch()
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            glossary.add_entry(file, line)
    if activate:
        update_user_config({"review": {"glossary": name}})
    return name


def glossary_use(name: str) -> None:
    """Make `name` the active glossary (created empty if new)."""
    file = glossary.library_file(name)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch()
    update_user_config({"review": {"glossary": name}})


def glossary_text(name: str) -> str:
    """The text of a library glossary, for export."""
    file = glossary.library_file(name)
    if not file.is_file():
        raise ValueError(f"Glossary not found: {name}")
    return file.read_text(encoding="utf-8")
