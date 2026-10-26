"""Glossary files: names and terms the transcription must get right.

Plain UTF-8 text, one entry per line:

    # comment
    Mariana Enacles          ← a term (kept exactly as written)
    polieste -> Poliéster    ← an explicit fix (also "→"); the right side is a term too

Sources are merged in order: the active glossary of the library
(`<config dir>/glossaries/<name>.txt`, config `review.glossary`), the project file
next to the media, then files or library names passed with --glossary. Later sources
win on fixes.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from legendaria_engine import paths

PROJECT_FILE = "legendaria-glossary.txt"
ARROWS = ("->", "→")
HEADER = (
    "# Legendária glossary: one term per line, or 'wrong -> right' for an explicit fix.\n"
    "# Lines starting with # are comments.\n"
)


def fold(text: str) -> str:
    """Lowercase without accents or surrounding punctuation, for comparisons."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return plain.strip(" .,;:!?\u00bf\u00a1\"'\u201c\u201d\u2018\u2019()[]\u2026-")


def split_entry(line: str) -> tuple[str, str] | str | None:
    """A parsed line: (wrong, right), a term, or None for blanks and comments."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    for arrow in ARROWS:
        if arrow in text:
            wrong, right = (part.strip() for part in text.split(arrow, 1))
            return (wrong, right) if wrong and right else None
    return text


@dataclass
class Glossary:
    """Merged terms (in order, unique) and explicit fixes keyed by folded wrong text."""

    terms: list[str] = field(default_factory=list)
    fixes: dict[str, str] = field(default_factory=dict)
    sources: list[Path] = field(default_factory=list)

    def add_term(self, term: str) -> None:
        """Add a term unless an equal one (ignoring case and accents) is there."""
        if fold(term) and all(fold(t) != fold(term) for t in self.terms):
            self.terms.append(term)

    def merge_text(self, text: str) -> None:
        """Add every entry of a glossary file's text."""
        for line in text.splitlines():
            entry = split_entry(line)
            if isinstance(entry, tuple):
                wrong, right = entry
                self.fixes[fold(wrong)] = right
                self.add_term(right)
            elif entry:
                self.add_term(entry)

    def __bool__(self) -> bool:
        return bool(self.terms or self.fixes)


DEFAULT_NAME = "default"
FORBIDDEN = set('/\\:*?"<>|')


def library_dir() -> Path:
    """Named glossaries live here: `<config dir>/glossaries/<name>.txt`."""
    return paths.config_dir() / "glossaries"


def safe_name(name: str) -> str:
    """A glossary name usable as a file name on every OS (raises ValueError otherwise)."""
    clean = name.strip()
    if not clean or clean.startswith(".") or any(ch in FORBIDDEN for ch in clean):
        raise ValueError(f"Invalid glossary name '{name}' (avoid / \\ : * ? \" < > |)")
    return clean


def library_file(name: str) -> Path:
    """File of a named glossary (it may not exist yet)."""
    return library_dir() / f"{safe_name(name)}.txt"


def migrate_legacy() -> None:
    """An old single `<config dir>/glossary.txt` becomes the glossary named "default"."""
    legacy = paths.config_dir() / "glossary.txt"
    target = library_file(DEFAULT_NAME)
    if legacy.is_file() and not target.exists():
        library_dir().mkdir(parents=True, exist_ok=True)
        legacy.rename(target)


def list_names() -> list[str]:
    """Names of the glossaries in the library, sorted."""
    migrate_legacy()
    folder = library_dir()
    return sorted(p.stem for p in folder.glob("*.txt")) if folder.is_dir() else []


def active_name() -> str:
    """The active glossary (config `review.glossary`, default "default")."""
    from legendaria_engine.config import load_config

    return load_config()["review"].get("glossary") or DEFAULT_NAME


def global_file() -> Path:
    """The active library glossary, used for every project."""
    migrate_legacy()
    return library_file(active_name())


def resolve(ref: str | Path) -> Path:
    """A glossary given as a file path or as the name of a library glossary."""
    path = Path(ref).expanduser()
    if path.is_file():
        return path
    try:
        named = library_file(str(ref))
    except ValueError:
        named = None
    if named is not None and named.is_file():
        return named
    raise FileNotFoundError(f"Glossary not found: no file or library glossary named '{ref}'")


def create(name: str) -> Path:
    """A new empty library glossary (with the explanatory header)."""
    path = library_file(name)
    if path.exists():
        raise FileExistsError(f"A glossary named '{name}' already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER, encoding="utf-8")
    return path


def import_file(source: Path, name: str | None = None, overwrite: bool = False) -> Path:
    """Copy a glossary file into the library (named after the file unless `name`)."""
    source = Path(source).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Glossary not found: {source}")
    Glossary().merge_text(source.read_text(encoding="utf-8"))  # must parse
    target = library_file(name or source.stem)
    if target.exists() and not overwrite:
        raise FileExistsError(f"A glossary named '{target.stem}' already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def export_file(name: str, destination: Path) -> Path:
    """Copy a library glossary to a file (to share it or back it up)."""
    source = library_file(name)
    if not source.is_file():
        raise FileNotFoundError(f"No glossary named '{name}'")
    destination = Path(destination).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def delete(name: str) -> None:
    """Remove a library glossary."""
    path = library_file(name)
    if not path.is_file():
        raise FileNotFoundError(f"No glossary named '{name}'")
    path.unlink()


def project_file(media: Path) -> Path:
    """The glossary next to a media file: `legendaria-glossary.txt`."""
    return Path(media).parent / PROJECT_FILE


def load(
    extra: list[Path] | None = None, media: Path | None = None, use_global: bool = True
) -> Glossary:
    """Active library glossary, then the project one next to `media`, then `extra`
    (files or library names)."""
    explicit = [resolve(p) for p in extra or []]
    candidates: list[Path] = []
    if use_global:
        candidates.append(global_file())
    if media is not None:
        candidates.append(project_file(media))
    glossary = Glossary()
    for path in candidates + explicit:
        if path.is_file():
            glossary.merge_text(path.read_text(encoding="utf-8"))
            glossary.sources.append(path)
        elif path in explicit:
            raise FileNotFoundError(f"Glossary not found: {path}")
    return glossary


def add_entry(path: Path, entry: str) -> bool:
    """Append a term or a 'wrong -> right' line; returns False if it was already there."""
    parsed = split_entry(entry)
    if parsed is None:
        raise ValueError("Empty glossary entry")
    path = Path(path)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    current = Glossary()
    current.merge_text(existing)
    if isinstance(parsed, tuple):
        if current.fixes.get(fold(parsed[0])) == parsed[1]:
            return False
        line = f"{parsed[0]} -> {parsed[1]}"
    else:
        if any(fold(t) == fold(parsed) for t in current.terms):
            return False
        line = parsed
    path.parent.mkdir(parents=True, exist_ok=True)
    text = existing if existing else HEADER
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n", encoding="utf-8")
    return True
