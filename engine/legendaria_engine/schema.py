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

    def merged_with(self, update: Transcript, start: float, end: float) -> Transcript:
        """A copy of this transcript where [start, end] comes from `update`.

        Works word by word, so a segment that crosses a boundary keeps only its words on
        its own side: no word is lost or duplicated. A word (or a segment without word
        timings) belongs to the range when its midpoint is inside. Used to regenerate
        part of a video (plan 02, stage 2c).
        """

        def inside(a: float, b: float) -> bool:
            return start <= (a + b) / 2 <= end

        def part(segments: list[Segment], want_inside: bool) -> list[Segment]:
            out = []
            for seg in segments:
                if not seg.words:
                    if inside(seg.start, seg.end) == want_inside:
                        out.append(seg)
                    continue
                words = [w for w in seg.words if inside(w.start, w.end) == want_inside]
                if words:
                    text = " ".join("".join(w.word for w in words).split())
                    out.append(Segment(words[0].start, words[-1].end, text, words))
            return out

        merged = part(self.segments, False) + part(update.segments, True)
        return Transcript(
            source=self.source,
            language=self.language,
            duration=self.duration,
            model=update.model,
            device=update.device,
            segments=sorted(merged, key=lambda s: s.start),
            language_probability=self.language_probability,
        )

    def save(self, path: Path) -> None:
        """Write as pretty UTF-8 JSON."""
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Transcript:
        """Read a transcript JSON file."""
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
