"""Transcript format (JSON v1): the contract between the engine and the Blender add-on."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


@dataclass
class Word:
    """One recognized word with its timing (seconds) and confidence."""

    start: float
    end: float
    word: str
    probability: float = 1.0


@dataclass
class Segment:
    """A sentence-like chunk of speech; becomes one subtitle cue."""

    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)


@dataclass
class Transcript:
    """The whole transcription of one media file (JSON v1)."""

    source: str
    language: str | None
    duration: float
    model: str
    device: str
    segments: list[Segment] = field(default_factory=list)
    language_probability: float | None = None
    version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Plain dict ready for JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transcript:
        """Build from a dict, rejecting other schema versions."""
        version = data.get("version")
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported transcript version {version!r} (expected {SCHEMA_VERSION})"
            )
        segments = [
            Segment(
                start=s["start"],
                end=s["end"],
                text=s["text"],
                words=[Word(**w) for w in s.get("words", [])],
            )
            for s in data["segments"]
        ]
        fields = {k: data[k] for k in ("source", "language", "duration", "model", "device")}
        return cls(
            **fields, segments=segments, language_probability=data.get("language_probability")
        )

    def save(self, path: Path) -> None:
        """Write as pretty UTF-8 JSON."""
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Transcript:
        """Read a transcript JSON file."""
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
