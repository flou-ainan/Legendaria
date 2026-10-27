"""Project file: the web editor's document, `<video>.legendaria.json` (ADR-016).

A project holds the source video, the kept ranges (what survives the cuts) and the cues,
all in **source time**. Cutting never touches the cues: `remap` moves them onto the output
timeline only when exporting, so undoing a cut brings its subtitles back.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from legendaria_engine.cues import Cue, CueList
from legendaria_engine.schema import Word

PROJECT_FORMAT = "legendaria-project"
PROJECT_VERSION = 1
SUFFIX = ".legendaria.json"
MIN_CUE = 0.08  # seconds; slivers left by a cut are dropped on export
MIN_RANGE = 0.01  # seconds; shorter kept ranges are dropped

Range = tuple[float, float]


class ProjectError(ValueError):
    """The project file is missing, unreadable or invalid."""


def project_path(video: Path) -> Path:
    """`clip.mp4` → `clip.mp4.legendaria.json`, next to the video."""
    return video.parent / f"{video.name}{SUFFIX}"


def normalize(ranges: list[Range], duration: float) -> list[Range]:
    """Sort, clip to [0, duration], merge overlapping ranges and drop empty ones."""
    clipped = sorted((max(0.0, float(a)), min(float(duration), float(b))) for a, b in ranges)
    merged: list[list[float]] = []
    for start, end in clipped:
        if end - start < MIN_RANGE:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(round(a, 3), round(b, 3)) for a, b in merged]


def remove_range(keep: list[Range], start: float, end: float) -> list[Range]:
    """The kept ranges after cutting out [start, end] (source time); tiny cuts are ignored."""
    if end - start < MIN_RANGE:
        return list(keep)
    out: list[Range] = []
    for a, b in keep:
        if end <= a or start >= b:
            out.append((a, b))
            continue
        if start - a >= MIN_RANGE:
            out.append((a, start))
        if b - end >= MIN_RANGE:
            out.append((end, b))
    return out


def output_duration(keep: list[Range]) -> float:
    """Length of the edited video: the sum of the kept ranges."""
    return round(sum(b - a for a, b in keep), 3)


def remap(cues: CueList, keep: list[Range]) -> CueList:
    """Cues on the output timeline: removed parts disappear, cues across a cut are clipped."""
    out: list[Cue] = []
    offset = 0.0
    for k_start, k_end in keep:
        for cue in cues.cues:
            start, end = max(cue.start, k_start), min(cue.end, k_end)
            if end - start >= MIN_CUE:
                shift = offset - k_start
                out.append(Cue(round(start + shift, 3), round(end + shift, 3), cue.text))
        offset += k_end - k_start
    return CueList(cues.style, cues.source, cues.language, out)


@dataclass
class Project:
    """The editor document. `source` is relative to the project file when possible."""

    source: str
    duration: float
    style: str
    language: str | None = None
    keep: list[Range] = field(default_factory=list)
    cues: list[Cue] = field(default_factory=list)
    look: dict[str, Any] = field(default_factory=dict)  # overrides of the style: font, size, y

    @classmethod
    def new(cls, video: Path, duration: float, cues: CueList) -> Project:
        """A fresh project for `video`: nothing cut, the cues as transcribed."""
        return cls(
            source=video.name,
            duration=round(duration, 3),
            style=cues.style,
            language=cues.language,
            keep=[(0.0, round(duration, 3))],
            cues=list(cues.cues),
        )

    def cue_list(self) -> CueList:
        """The cues (source time) as a CueList."""
        return CueList(self.style, self.source, self.language, list(self.cues))

    def edited_cues(self) -> CueList:
        """The cues on the output timeline (after the cuts)."""
        return remap(self.cue_list(), self.keep)

    def to_dict(self) -> dict[str, Any]:
        """Plain dict ready for JSON (see schemas/project.schema.json)."""
        return {
            "format": PROJECT_FORMAT,
            "version": PROJECT_VERSION,
            "source": self.source,
            "duration": self.duration,
            "style": self.style,
            "language": self.language,
            "keep": [[a, b] for a, b in self.keep],
            "cues": [_cue_dict(c) for c in self.cues],
            "look": self.look,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        """Validate and build; ranges are normalized, cues sorted by start."""
        if not isinstance(data, dict) or data.get("format") != PROJECT_FORMAT:
            raise ProjectError('Not a Legendária project (missing "format": "legendaria-project")')
        if data.get("version") != PROJECT_VERSION:
            raise ProjectError(f"Unsupported project version {data.get('version')!r}")
        try:
            duration = float(data["duration"])
            keep = normalize([(a, b) for a, b in data.get("keep", [])], duration)
            cues = sorted(
                (
                    Cue(
                        float(c["start"]),
                        float(c["end"]),
                        str(c["text"]),
                        [Word(**w) for w in c.get("words", [])],
                    )
                    for c in data.get("cues", [])
                ),
                key=lambda c: c.start,
            )
            for cue in cues:
                if cue.end < cue.start:
                    raise ProjectError(f"Cue ends before it starts: {cue.text!r}")
            return cls(
                source=str(data["source"]),
                duration=duration,
                style=str(data.get("style", "custom")),
                language=data.get("language"),
                keep=keep,
                cues=cues,
                look=clean_look(data.get("look")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, ProjectError):
                raise
            raise ProjectError(f"Invalid project: {exc}") from exc

    @classmethod
    def load(cls, path: Path) -> Project:
        """Read a project file."""
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProjectError(f"Could not read {path}: {exc}") from exc
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        """Write atomically (temp file + rename), so a crash never leaves half a project."""
        path = Path(path)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, path)


HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
LOOK_SIZE = (0.3, 3.0)  # allowed multiplier of the style's font size


def clean_look(raw: Any) -> dict[str, Any]:
    """The project's look overrides, validated: `font` (family), `size` (multiplier), `y` (0 bottom to 1 top), `color` and `outline_color` (`#rrggbb`), `box` and `uppercase` (bool)."""
    if not isinstance(raw, dict):
        return {}
    look: dict[str, Any] = {}
    if isinstance(raw.get("font"), str) and raw["font"].strip():
        look["font"] = raw["font"].strip()
    if isinstance(raw.get("size"), int | float):
        look["size"] = min(max(float(raw["size"]), LOOK_SIZE[0]), LOOK_SIZE[1])
    if isinstance(raw.get("y"), int | float):
        look["y"] = min(max(float(raw["y"]), 0.0), 1.0)
    for key in ("color", "outline_color"):
        if isinstance(raw.get(key), str) and HEX_COLOR.fullmatch(raw[key]):
            look[key] = raw[key].lower()
    for key in ("box", "uppercase"):
        if isinstance(raw.get(key), bool):
            look[key] = raw[key]
    return look


def _cue_dict(cue: Cue) -> dict[str, Any]:
    data: dict[str, Any] = {"start": cue.start, "end": cue.end, "text": cue.text}
    if cue.words:
        data["words"] = [
            {"start": w.start, "end": w.end, "word": w.word, "probability": w.probability}
            for w in cue.words
        ]
    return data
