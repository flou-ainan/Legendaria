"""Cues: the timed text blocks shown on screen, built from word timings by a style.

`captions` gives short CapCut-style phrases; `subtitles` gives film-style lines.
Styles are plain dicts from the config's "styles" section (see defaults/config.json).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

from legendaria_engine.schema import Transcript, Word

CUES_VERSION = 1


@dataclass
class Cue:
    """One block of text on screen, with the words it contains."""

    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)
    look: dict[str, Any] = field(default_factory=dict)  # this cue's own look overrides (ADR-022)


@dataclass
class CueList:
    """Cues for one media file in one style (cues JSON v1)."""

    style: str
    source: str
    language: str | None
    cues: list[Cue] = field(default_factory=list)
    version: int = CUES_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Plain dict ready for JSON (a cue's `look` only when it has one)."""
        data = asdict(self)
        for cue in data["cues"]:
            if not cue["look"]:
                del cue["look"]
        return data

    def save(self, path: Path) -> None:
        """Write as pretty UTF-8 JSON."""
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CueList:
        """Build from a cues JSON v1 dict (words are optional)."""
        if data.get("version") != CUES_VERSION:
            raise ValueError(f"Unsupported cues version {data.get('version')!r}")
        cues = [
            Cue(
                float(c["start"]),
                float(c["end"]),
                str(c["text"]),
                [Word(**w) for w in c.get("words", [])],
            )
            for c in data.get("cues", [])
        ]
        return cls(
            style=data.get("style", "custom"),
            source=data.get("source", ""),
            language=data.get("language"),
            cues=cues,
        )


def _join(words: list[Word]) -> str:
    """Concatenate words as Whisper spells them: a leading space marks a new word,
    so attached pieces such as "-se" or "'s" stay glued to the previous word."""
    return " ".join("".join(w.word for w in words).split())


def _ends_with(word: Word, chars: str) -> bool:
    text = word.word.strip()
    return bool(text) and bool(chars) and text[-1] in chars


def _is_attached(word: Word) -> bool:
    """A piece Whisper glued to the previous word (no leading space): "-vindas", "'s"."""
    return bool(word.word) and not word.word[0].isspace()


def _units(words: list[Word]) -> int:
    """Readable words: attached pieces do not count ("bem" + "-vindas" is one)."""
    return 1 + sum(1 for w in words[1:] if not _is_attached(w)) if words else 0


def _letters(words: list[Word]) -> int:
    return sum(ch.isalnum() for ch in _join(words))


def make_cues(transcript: Transcript, style: dict[str, Any], style_name: str = "custom") -> CueList:
    """Chunk the transcript's words into cues that respect the style's limits.

    Style keys (all optional): max_words (readable words; attached pieces like "-vindas"
    never split from their word), max_chars, max_duration, min_duration, pause_break
    (seconds of silence that force a break), break_after (punctuation characters that
    end a cue), break_on_segment (start a new cue at each segment), join_short (a single
    word with at most this many letters, like "a", "de", "no", may take the next word
    even beyond max_words), fill_gaps (extend a cue to the next one when the silence
    between them is at most this many seconds, so the screen does not blink).
    """
    max_words = style.get("max_words")
    max_chars = style.get("max_chars")
    max_duration = style.get("max_duration")
    pause_break = style.get("pause_break")
    break_after = style.get("break_after", "")
    break_on_segment = style.get("break_on_segment", True)
    join_short = style.get("join_short")

    cues: list[Cue] = []
    current: list[Word] = []

    def flush() -> None:
        if current:
            cues.append(Cue(current[0].start, current[-1].end, _join(current), list(current)))
            current.clear()

    for segment in transcript.segments:
        if not segment.words:  # no word timings: keep the whole segment as one cue
            flush()
            if segment.text.strip():
                cues.append(Cue(segment.start, segment.end, segment.text.strip()))
            continue
        if break_on_segment:
            flush()
        for word in segment.words:
            if current and _is_attached(word):
                current.append(word)  # glued piece: never starts a new cue
                if _ends_with(word, break_after):
                    flush()
                continue
            if current:
                allowed = max_words
                if (
                    allowed is not None
                    and join_short
                    and _units(current) == 1
                    and _letters(current) <= join_short
                    and not _ends_with(current[-1], break_after)
                ):
                    allowed += 1  # short word ("de", "a") takes the next one
                too_many = allowed is not None and _units(current) + 1 > allowed
                too_long = max_chars is not None and len(_join([*current, word])) > max_chars
                too_slow = max_duration is not None and word.end - current[0].start > max_duration
                paused = pause_break is not None and word.start - current[-1].end > pause_break
                if too_many or too_long or too_slow or paused:
                    flush()
            current.append(word)
            if _ends_with(word, break_after):
                flush()
    flush()
    _fill_gaps(cues, style.get("fill_gaps"))
    _apply_min_duration(cues, style.get("min_duration"))
    return CueList(
        style=style_name, source=transcript.source, language=transcript.language, cues=cues
    )


def _fill_gaps(cues: list[Cue], max_gap: float | None) -> None:
    """Extend each cue to the next one's start when the silence between them is short."""
    if not max_gap:
        return
    for cue, nxt in pairwise(cues):
        if 0 < nxt.start - cue.end <= max_gap:
            cue.end = nxt.start


def _apply_min_duration(cues: list[Cue], min_duration: float | None) -> None:
    """Stretch cues shorter than `min_duration`, without overlapping the next cue."""
    if not min_duration:
        return
    for i, cue in enumerate(cues):
        if cue.end - cue.start < min_duration:
            limit = cues[i + 1].start if i + 1 < len(cues) else cue.start + min_duration
            cue.end = round(max(cue.end, min(cue.start + min_duration, limit)), 3)


def wrap_lines(text: str, line_length: int | None) -> str:
    """Split text into two balanced lines when it is longer than `line_length`."""
    if not line_length or len(text) <= line_length or " " not in text:
        return text
    middle = len(text) // 2
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    split = min(spaces, key=lambda i: abs(i - middle))
    return text[:split] + "\n" + text[split + 1 :]
