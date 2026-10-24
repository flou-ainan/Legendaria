"""Subtitle writers: transcript → SRT / VTT text."""

from __future__ import annotations

from legendaria_engine.schema import Transcript

FORMATS = ("json", "srt", "vtt")


def format_timestamp(seconds: float, separator: str = ",") -> str:
    """`HH:MM:SS,mmm` (SRT) or `HH:MM:SS.mmm` (VTT). Hours keep counting past 24."""
    total_ms = max(0, round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"


def to_srt(transcript: Transcript) -> str:
    """Numbered SRT cues, one per segment."""
    blocks = []
    for index, seg in enumerate(transcript.segments, start=1):
        start, end = format_timestamp(seg.start), format_timestamp(seg.end)
        blocks.append(f"{index}\n{start} --> {end}\n{seg.text.strip()}\n")
    return "\n".join(blocks)


def to_vtt(transcript: Transcript) -> str:
    """WebVTT cues, one per segment."""
    blocks = ["WEBVTT\n"]
    for seg in transcript.segments:
        start, end = format_timestamp(seg.start, "."), format_timestamp(seg.end, ".")
        blocks.append(f"{start} --> {end}\n{seg.text.strip()}\n")
    return "\n".join(blocks)


WRITERS = {"srt": to_srt, "vtt": to_vtt}
