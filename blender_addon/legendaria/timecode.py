# SPDX-License-Identifier: GPL-3.0-or-later
"""Frames ↔ seconds and SRT/VTT text. Pure Python (no bpy), so it can be unit-tested.

The timestamp format matches the engine's `formats.py` (ADR-003: the add-on cannot
import the engine, so this small piece is duplicated on purpose).
"""

from __future__ import annotations


def seconds_to_frame(seconds: float, fps: float, offset: int = 0) -> int:
    """Frame number for a time in seconds, counted from `offset` (the media's first frame)."""
    return offset + round(seconds * fps)


def frame_to_seconds(frame: int, fps: float, offset: int = 0) -> float:
    """Seconds from `offset` to `frame`."""
    return (frame - offset) / fps


def format_timestamp(seconds: float, separator: str = ",") -> str:
    """`HH:MM:SS,mmm` (SRT) or `HH:MM:SS.mmm` (VTT). Hours keep counting past 24."""
    total_ms = max(0, round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"


def to_srt(cues: list[tuple[float, float, str]]) -> str:
    """SRT text from (start, end, text) tuples."""
    blocks = [
        f"{i}\n{format_timestamp(s)} --> {format_timestamp(e)}\n{t.strip()}\n"
        for i, (s, e, t) in enumerate(cues, start=1)
    ]
    return "\n".join(blocks)


def to_vtt(cues: list[tuple[float, float, str]]) -> str:
    """WebVTT text from (start, end, text) tuples."""
    blocks = ["WEBVTT\n"]
    blocks += [
        f"{format_timestamp(s, '.')} --> {format_timestamp(e, '.')}\n{t.strip()}\n"
        for s, e, t in cues
    ]
    return "\n".join(blocks)
