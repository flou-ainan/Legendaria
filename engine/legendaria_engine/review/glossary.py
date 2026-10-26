"""Glossary files: names and terms the transcription must get right.

Plain UTF-8 text, one entry per line:

    # comment
    Mariana Enacles          ← a term (kept exactly as written)
    polieste -> Poliéster    ← an explicit fix (also "→"); the right side is a term too

Files are merged in order (global first, then project ones); later files win on fixes.
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


def global_file() -> Path:
    """The user's glossary for every project: `<config dir>/glossary.txt`."""
    return paths.config_dir() / "glossary.txt"


def project_file(media: Path) -> Path:
    """The glossary next to a media file: `legendaria-glossary.txt`."""
    return Path(media).parent / PROJECT_FILE


def load(
    extra: list[Path] | None = None, media: Path | None = None, use_global: bool = True
) -> Glossary:
    """Global glossary, then the project one next to `media`, then `extra` files."""
    explicit = [Path(p).expanduser() for p in extra or []]
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
