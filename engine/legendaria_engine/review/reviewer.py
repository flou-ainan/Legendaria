"""Layer 3: turn an LLM's corrected lines into guarded, word-level suggestions.

The model sees batches of lines (with context lines around them), the glossary, and the
words Whisper was unsure about marked [[like this]]. Its answer is diffed against the
original, word by word; each changed block becomes a suggestion only if the guard allows
it, so the model cannot rewrite what the speaker said.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from legendaria_engine import paths
from legendaria_engine.events import Reporter
from legendaria_engine.review.glossary import Glossary, fold
from legendaria_engine.review.llm import LLMClient, LLMError
from legendaria_engine.review.suggestions import Suggestion
from legendaria_engine.schema import Transcript

EDGE_PUNCT = ".,;:!?\u2026\"'\u201c\u201d\u2018\u2019()[]-"


@dataclass
class Unit:
    """A readable word: one or more Whisper words glued together ("bem" + "-vindas")."""

    first: int
    last: int  # exclusive word index
    text: str
    confidence: float


def units_of(words) -> list[Unit]:
    """Group a segment's words into readable units."""
    units: list[Unit] = []
    for i, w in enumerate(words):
        if units and w.word[:1] and not w.word[:1].isspace():
            u = units[-1]
            units[-1] = Unit(
                u.first, i + 1, u.text + w.word.strip(), min(u.confidence, w.probability)
            )
        else:
            units.append(Unit(i, i + 1, w.word.strip(), w.probability))
    return units


def _key(token: str) -> str:
    """Comparison key that keeps accents (so accent fixes show up as changes)."""
    return token.casefold().strip(EDGE_PUNCT)


def _is_glossary(text: str, glossary: Glossary) -> bool:
    folded = fold(text)
    return bool(folded) and any(
        folded == fold(t) or folded in fold(t).split() for t in glossary.terms
    )


MIN_SIMILARITY = 0.5  # a correction must still sound like what was heard


def guard(old: list[Unit], new: list[str], glossary: Glossary, low_confidence: float) -> str | None:
    """Why a changed block is acceptable, or None to reject it.

    Accepted: accent/case/punctuation-only fixes; otherwise the new text must resemble
    the old one (so the model cannot invent or translate) AND either the recognizer was
    unsure about the old words or the new text is a glossary term. Dropping words is
    never accepted (fillers were really said).
    """
    if old and not new:
        return None
    old_text = " ".join(u.text for u in old)
    new_text = " ".join(new)
    if old and new and fold(old_text) == fold(new_text):
        return "accents, case or punctuation"
    if SequenceMatcher(None, fold(old_text), fold(new_text)).ratio() < MIN_SIMILARITY:
        return None
    if new and _is_glossary(new_text, glossary):
        return "glossary term"
    if old and any(u.confidence < low_confidence for u in old):
        return "word the recognizer was unsure about"
    return None


def line_for_prompt(units: list[Unit], low_confidence: float) -> str:
    """Line text with uncertain words marked [[like this]]."""
    return " ".join(f"[[{u.text}]]" if u.confidence < low_confidence else u.text for u in units)


def diff_suggestions(
    seg_index: int,
    segment,
    corrected: str,
    glossary: Glossary,
    low_confidence: float,
    max_change_ratio: float,
) -> tuple[list[Suggestion], int]:
    """(suggestions, rejected count) for one segment and the model's version of it."""
    units = units_of(segment.words)
    new = re.sub(r"\[\[|\]\]", "", corrected).split()
    if not units or not new:
        return [], 0
    old_keys, new_keys = [_key(u.text) for u in units], [_key(t) for t in new]
    matcher = SequenceMatcher(None, old_keys, new_keys, autojunk=False)
    original = " ".join(u.text for u in units)
    if 1 - SequenceMatcher(None, original, " ".join(new)).ratio() > max_change_ratio:
        return [], 1  # the model rewrote the line
    out, rejected = [], 0
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":  # same word (case and edge punctuation ignored): no suggestion
            continue
        old_block, new_block = units[i1:i2], new[j1:j2]
        if not old_block:  # insertion: attach to the previous (or next) unit
            anchor = units[i1 - 1] if i1 > 0 else units[i1]
            old_block = [anchor]
            new_block = [anchor.text, *new_block] if i1 > 0 else [*new_block, anchor.text]
        reason = guard(old_block, new_block, glossary, low_confidence)
        if reason is None:
            rejected += 1
            continue
        out.append(_make(seg_index, segment, old_block, " ".join(new_block), f"LLM: {reason}"))
    return out, rejected


def _make(seg_index, segment, block: list[Unit], after: str, reason: str) -> Suggestion:
    words = segment.words[block[0].first : block[-1].last]
    return Suggestion(
        id=0,
        segment=seg_index,
        first=block[0].first,
        last=block[-1].last,
        start=words[0].start,
        end=words[-1].end,
        before=" ".join(u.text for u in block),
        after=after,
        source="llm",
        reason=reason,
    )


def build_prompt(lines: list[str], targets: range, language: str | None, glossary: Glossary) -> str:
    """Fill the editable prompt template (`defaults/review_prompt.txt`, user copy wins)."""
    user = paths.config_dir() / "review_prompt.txt"
    template = (user if user.is_file() else paths.defaults_dir() / "review_prompt.txt").read_text(
        encoding="utf-8"
    )
    numbered = "\n".join(
        f"{n + 1}{'' if n in targets else ' (context)'}: {text}" for n, text in enumerate(lines)
    )
    return template.format(
        language=language or "same as the text",
        glossary=", ".join(glossary.terms) or "(none)",
        count=len(lines),
        lines=numbered,
    )


def fixes_by_line(answer: dict, count: int) -> dict[int, str]:
    """{0-based line offset: corrected text} from {"fixes": {"<1-based n>": text}}.

    Lines the model did not list are unchanged. A full {"lines": [...]} answer (older
    prompt) is accepted when it has the right length.
    """
    fixes = answer.get("fixes")
    if isinstance(fixes, dict):
        out = {}
        for key, text in fixes.items():
            if isinstance(text, str) and str(key).strip().isdigit() and 1 <= int(key) <= count:
                out[int(key) - 1] = text
        return out
    lines = answer.get("lines")
    if isinstance(lines, list) and len(lines) == count:
        return {i: t for i, t in enumerate(lines) if isinstance(t, str)}
    raise LLMError("the answer has no 'fixes' object")


def review(
    transcript: Transcript,
    client: LLMClient,
    glossary: Glossary,
    reporter: Reporter,
    low_confidence: float = 0.5,
    batch_lines: int = 20,
    context_lines: int = 2,
    max_change_ratio: float = 0.35,
) -> tuple[list[Suggestion], int]:
    """LLM suggestions for the whole transcript; returns (suggestions, rejected count)."""
    segments = transcript.segments
    total = len(segments)
    found: list[Suggestion] = []
    rejected = 0
    for start in range(0, total, batch_lines):
        end = min(total, start + batch_lines)
        lo, hi = max(0, start - context_lines), min(total, end + context_lines)
        lines = [
            line_for_prompt(units_of(s.words), low_confidence) if s.words else s.text
            for s in segments[lo:hi]
        ]
        targets = range(start - lo, end - lo)
        try:
            answer = client.chat_json(build_prompt(lines, targets, transcript.language, glossary))
            corrected = fixes_by_line(answer, len(lines))
        except LLMError as exc:
            reporter.warning(f"Review batch {start + 1}-{end} skipped: {exc}")
            reporter.emit("review_progress", done=end, total=total)
            continue
        for offset in targets:
            index = lo + offset
            if not segments[index].words or offset not in corrected:
                continue
            suggestions, bad = diff_suggestions(
                index,
                segments[index],
                corrected[offset],
                glossary,
                low_confidence,
                max_change_ratio,
            )
            found += suggestions
            rejected += bad
        reporter.emit("review_progress", done=end, total=total)
    return found, rejected


def describe(settings) -> str:
    """Short provider/model label for logs."""
    return json.dumps(
        {"provider": settings.provider, "model": settings.model, "url": settings.base_url}
    )
