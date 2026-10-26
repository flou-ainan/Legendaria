"""Layer 2: glossary-based corrections without AI.

1. Explicit fixes: "wrong -> right" lines in the glossary (one or more words).
2. Fuzzy matches: a word (or run of words) the model was unsure about that looks
   like a glossary term, ignoring case and accents ("polieste" → "Poliéster").
"""

from __future__ import annotations

from difflib import SequenceMatcher

from legendaria_engine.review.glossary import Glossary, fold
from legendaria_engine.review.suggestions import Suggestion
from legendaria_engine.schema import Transcript, Word

MAX_SPAN = 4  # longest run of words compared with a multi-word term or fix


def _trailing(text: str) -> str:
    """Punctuation at the end of a word, kept on the replacement ("polieste." → "Poliéster.")."""
    stripped = text.rstrip(".,;:!?\u2026\"'\u201d\u2019)")
    return text[len(stripped) :]


def match_case(original: str, replacement: str) -> str:
    """Keep a capital first letter from the original ("Bolsa Bet" + "bolsa Beth" → "Bolsa Beth")."""
    if original[:1].isupper() and replacement[:1].islower():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _span_text(words: list[Word]) -> str:
    return " ".join("".join(w.word for w in words).split())


def similarity(a: str, b: str) -> float:
    """Ratio of two strings after folding case, accents and edge punctuation."""
    return SequenceMatcher(None, fold(a), fold(b)).ratio()


def suggest(
    transcript: Transcript,
    glossary: Glossary,
    threshold: float = 0.82,
    low_confidence: float = 0.5,
    start_id: int = 1,
) -> list[Suggestion]:
    """Suggestions for every segment; explicit fixes first, then fuzzy matches."""
    out: list[Suggestion] = []
    next_id = start_id
    term_lengths = {t: len(t.split()) for t in glossary.terms}
    for seg_index, segment in enumerate(transcript.segments):
        words = segment.words
        taken = [False] * len(words)
        candidates: list[tuple[int, int, str, str]] = []  # first, last, after, reason
        # 1. explicit fixes, longest spans first
        for size in range(min(MAX_SPAN, len(words)), 0, -1):
            for first in range(len(words) - size + 1):
                span = words[first : first + size]
                right = glossary.fixes.get(fold(_span_text(span)))
                if right and not any(taken[first : first + size]):
                    candidates.append((first, first + size, right, "glossary fix"))
                    taken[first : first + size] = [True] * size
        # 2. fuzzy matches on uncertain words
        for term, size in term_lengths.items():
            for first in range(len(words) - size + 1):
                span = words[first : first + size]
                if any(taken[first : first + size]):
                    continue
                if min(w.probability for w in span) >= low_confidence:
                    continue
                text = _span_text(span)
                if fold(text) == fold(term) or len(fold(text)) < 3:
                    continue
                limit = threshold if len(fold(term)) > 4 else max(threshold, 0.85)
                if similarity(text, term) >= limit:
                    candidates.append(
                        (first, first + size, term, f"sounds like glossary term '{term}'")
                    )
                    taken[first : first + size] = [True] * size
        for first, last, right, reason in sorted(candidates):
            span = words[first:last]
            before = _span_text(span)
            after = match_case(before, right) + _trailing(before)
            if after == before:
                continue
            out.append(
                Suggestion(
                    id=next_id,
                    segment=seg_index,
                    first=first,
                    last=last,
                    start=span[0].start,
                    end=span[-1].end,
                    before=before,
                    after=after,
                    source="glossary",
                    reason=reason,
                )
            )
            next_id += 1
    return out
