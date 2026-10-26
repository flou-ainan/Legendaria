"""Layer 1: glossary terms as Whisper `hotwords`, which steer recognition toward them."""

from __future__ import annotations

from legendaria_engine.review.glossary import Glossary

# Whisper's prompt holds about 224 tokens; a few characters per token, minus room
# for the decoder's own context. Terms beyond the budget are left out (first wins).
MAX_CHARS = 600


def hotwords(glossary: Glossary, max_chars: int = MAX_CHARS) -> str | None:
    """Comma-separated terms within the budget, or None when there are none."""
    chosen: list[str] = []
    size = 0
    for term in glossary.terms:
        extra = len(term) + (2 if chosen else 0)
        if size + extra > max_chars:
            break
        chosen.append(term)
        size += extra
    return ", ".join(chosen) or None
