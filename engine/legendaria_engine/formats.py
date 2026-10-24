"""Subtitle writers: cues → SRT / VTT text."""

from __future__ import annotations

from legendaria_engine.cues import CueList, wrap_lines

FORMATS = ("json", "cues", "srt", "vtt")


def format_timestamp(seconds: float, separator: str = ",") -> str:
    """`HH:MM:SS,mmm` (SRT) or `HH:MM:SS.mmm` (VTT). Hours keep counting past 24."""
    total_ms = max(0, round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"


def to_srt(cues: CueList, line_length: int | None = None) -> str:
    """Numbered SRT blocks, one per cue; long cues wrap into two lines."""
    blocks = []
    for index, cue in enumerate(cues.cues, start=1):
        start, end = format_timestamp(cue.start), format_timestamp(cue.end)
        blocks.append(f"{index}\n{start} --> {end}\n{wrap_lines(cue.text, line_length)}\n")
    return "\n".join(blocks)


def to_vtt(cues: CueList, line_length: int | None = None) -> str:
    """WebVTT blocks, one per cue; long cues wrap into two lines."""
    blocks = ["WEBVTT\n"]
    for cue in cues.cues:
        start, end = format_timestamp(cue.start, "."), format_timestamp(cue.end, ".")
        blocks.append(f"{start} --> {end}\n{wrap_lines(cue.text, line_length)}\n")
    return "\n".join(blocks)


WRITERS = {"srt": to_srt, "vtt": to_vtt}
