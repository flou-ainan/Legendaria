"""Review document (`<name>.review.json`, v1): suggested corrections to accept or reject."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from legendaria_engine.review.align import replace_words
from legendaria_engine.schema import Transcript

REVIEW_VERSION = 1
STATUSES = ("pending", "accepted", "rejected")


@dataclass
class Suggestion:
    """Replace words[first:last] of one segment ("before") with "after"."""

    id: int
    segment: int
    first: int
    last: int
    start: float
    end: float
    before: str
    after: str
    source: str  # "glossary" (fix rule or fuzzy match) or "llm"
    reason: str = ""
    status: str = "pending"


@dataclass
class Review:
    """All suggestions for one transcript file."""

    transcript: str  # path of the transcript JSON the suggestions refer to
    suggestions: list[Suggestion] = field(default_factory=list)
    version: int = REVIEW_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Plain dict ready for JSON."""
        return asdict(self)

    def save(self, path: Path) -> None:
        """Write as pretty UTF-8 JSON."""
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Review:
        """Read a review JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("version") != REVIEW_VERSION:
            raise ValueError(f"Unsupported review version {data.get('version')!r}")
        return cls(
            transcript=data["transcript"],
            suggestions=[Suggestion(**s) for s in data["suggestions"]],
        )


def apply(transcript: Transcript, suggestions: list[Suggestion]) -> Transcript:
    """A copy of the transcript with the given suggestions applied (word timings re-spread).

    Suggestions are applied from the end of each segment backwards, so earlier word
    indices stay valid; overlapping suggestions in a segment keep only the first one.
    """
    segments = list(transcript.segments)
    by_segment: dict[int, list[Suggestion]] = {}
    for s in suggestions:
        by_segment.setdefault(s.segment, []).append(s)
    for index, items in by_segment.items():
        taken: list[Suggestion] = []
        for s in sorted(items, key=lambda s: s.first):
            if all(s.first >= t.last for t in taken):
                taken.append(s)
        segment = segments[index]
        for s in sorted(taken, key=lambda s: s.first, reverse=True):
            segment = replace_words(segment, s.first, s.last, s.after)
        segments[index] = segment
    return Transcript(
        source=transcript.source,
        language=transcript.language,
        duration=transcript.duration,
        model=transcript.model,
        device=transcript.device,
        segments=segments,
        language_probability=transcript.language_probability,
    )
