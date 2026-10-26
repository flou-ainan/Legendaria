"""Replace words in a transcript and give the new words sensible timings."""

from __future__ import annotations

from legendaria_engine.schema import Segment, Word


def retime(old: list[Word], new_text: str) -> list[Word]:
    """Words for `new_text` spread over the time span of `old`, in proportion to length.

    The first new word keeps the leading space of the first old word (so attached
    pieces stay attached); confidence is set to 1.0 because a person or a rule chose it.
    """
    tokens = new_text.split()
    if not old:
        raise ValueError("Nothing to replace")
    if not tokens:
        return []
    start, end = old[0].start, old[-1].end
    total = sum(len(t) for t in tokens) or 1
    leading = " " if old[0].word[:1].isspace() else ""
    words, cursor = [], start
    for i, token in enumerate(tokens):
        span = (end - start) * len(token) / total
        stop = end if i == len(tokens) - 1 else round(cursor + span, 3)
        words.append(Word(round(cursor, 3), stop, (leading if i == 0 else " ") + token, 1.0))
        cursor = stop
    return words


def segment_text(words: list[Word]) -> str:
    """Segment text rebuilt from its words (as Whisper spells them)."""
    return " ".join("".join(w.word for w in words).split())


def replace_words(segment: Segment, first: int, last: int, new_text: str) -> Segment:
    """A copy of `segment` with words[first:last] replaced by `new_text`."""
    words = (
        segment.words[:first] + retime(segment.words[first:last], new_text) + segment.words[last:]
    )
    return Segment(segment.start, segment.end, segment_text(words), words)
