import pytest

from legendaria_engine.config import load_config
from legendaria_engine.cues import make_cues, wrap_lines
from legendaria_engine.schema import Segment, Transcript, Word


def words(*items):
    """items: (text, start, end)"""
    return [Word(start=s, end=e, word=f" {t}") for t, s, e in items]


def transcript(*segments):
    return Transcript(
        source="a.mp4",
        language="pt",
        duration=60,
        model="small",
        device="cpu",
        segments=list(segments),
    )


def segment(ws):
    return Segment(ws[0].start, ws[-1].end, " ".join(w.word.strip() for w in ws), ws)


def texts(cue_list):
    return [c.text for c in cue_list.cues]


def test_max_words():
    ws = words(*[(f"w{i}", i * 0.2, i * 0.2 + 0.15) for i in range(10)])
    result = make_cues(transcript(segment(ws)), {"max_words": 4}, "captions")
    assert texts(result) == ["w0 w1 w2 w3", "w4 w5 w6 w7", "w8 w9"]
    assert result.style == "captions"


def test_max_chars_and_duration():
    ws = words(("alpha", 0, 0.5), ("beta", 0.5, 1.0), ("gamma", 1.0, 1.5), ("delta", 3.0, 3.5))
    assert texts(make_cues(transcript(segment(ws)), {"max_chars": 11})) == [
        "alpha beta",
        "gamma delta",
    ]
    assert texts(make_cues(transcript(segment(ws)), {"max_duration": 1.2})) == [
        "alpha beta",
        "gamma",
        "delta",
    ]


def test_breaks_after_punctuation_and_on_pauses():
    ws = words(("Oi,", 0, 0.3), ("tudo", 0.35, 0.6), ("bem?", 0.6, 0.9), ("Sim", 2.0, 2.3))
    result = make_cues(transcript(segment(ws)), {"break_after": ",?", "pause_break": 0.5})
    assert texts(result) == ["Oi,", "tudo bem?", "Sim"]
    ws2 = words(("um", 0, 0.2), ("dois", 1.5, 1.7))
    assert texts(make_cues(transcript(segment(ws2)), {"pause_break": 0.5})) == ["um", "dois"]


def test_segments_start_new_cues_unless_disabled():
    t = transcript(segment(words(("a", 0, 0.1))), segment(words(("b", 0.2, 0.3))))
    assert texts(make_cues(t, {})) == ["a", "b"]
    assert texts(make_cues(t, {"break_on_segment": False})) == ["a b"]


def test_min_duration_stretches_without_overlap():
    ws = words(("a", 0.0, 0.1), ("b", 0.25, 0.3), ("c", 2.0, 2.05))
    result = make_cues(transcript(segment(ws)), {"max_words": 1, "min_duration": 0.5})
    assert [(c.start, c.end) for c in result.cues] == [(0.0, 0.25), (0.25, 0.75), (2.0, 2.5)]


def test_segment_without_words_is_kept_whole():
    t = transcript(Segment(0, 3, " Sem palavras aqui.", []))
    result = make_cues(t, {"max_words": 1})
    assert texts(result) == ["Sem palavras aqui."]
    assert result.cues[0].words == []


def test_default_styles_produce_short_captions_and_long_subtitles():
    config = load_config()
    ws = words(*[(f"palavra{i}", i * 0.3, i * 0.3 + 0.25) for i in range(12)])
    t = transcript(segment(ws))
    captions = make_cues(t, config["styles"]["captions"], "captions")
    subtitles = make_cues(t, config["styles"]["subtitles"], "subtitles")
    assert all(len(c.words) <= 4 and len(c.text) <= 22 for c in captions.cues)
    assert all(c.end - c.start <= 2.2 + 1e-9 for c in captions.cues)
    assert len(subtitles.cues) < len(captions.cues)


@pytest.mark.parametrize(
    ("text", "length", "expected"),
    [
        ("short", 42, "short"),
        ("one two three four", 10, "one two\nthree four"),
        ("nospaceshere", 4, "nospaceshere"),
        ("any", None, "any"),
    ],
)
def test_wrap_lines(text, length, expected):
    assert wrap_lines(text, length) == expected


def test_attached_pieces_stay_glued():
    ws = [
        Word(0, 0.2, " Descreve"),
        Word(0.2, 0.3, "-se"),
        Word(0.3, 0.5, " o"),
        Word(0.5, 0.7, " Tom's"),
    ]
    assert texts(make_cues(transcript(segment(ws)), {})) == ["Descreve-se o Tom's"]


def test_attached_pieces_never_start_a_cue():
    ws = [
        Word(0, 0.3, " bem"),
        Word(0.3, 0.6, "-vindas"),
        Word(0.7, 1.0, " ao"),
        Word(1.0, 1.3, " canal"),
    ]
    result = make_cues(transcript(segment(ws)), {"max_words": 1})
    assert texts(result) == ["bem-vindas", "ao", "canal"]


def test_short_words_pair_with_the_next():
    ws = words(
        ("a", 0, 0.1),
        ("bolsa", 0.1, 0.5),
        ("de", 0.5, 0.6),
        ("crochê", 0.6, 1.0),
        ("linda", 1.0, 1.4),
    )
    result = make_cues(transcript(segment(ws)), {"max_words": 1, "join_short": 3})
    assert texts(result) == ["a bolsa", "de crochê", "linda"]


def test_short_word_ending_a_sentence_does_not_pair():
    ws = words(("é.", 0, 0.2), ("Agora", 0.3, 0.6))
    result = make_cues(
        transcript(segment(ws)), {"max_words": 1, "join_short": 3, "break_after": "."}
    )
    assert texts(result) == ["é.", "Agora"]


def test_fill_gaps_closes_short_silences_only():
    ws = words(("um", 0.0, 0.2), ("dois", 0.4, 0.6), ("três", 2.0, 2.2))
    result = make_cues(transcript(segment(ws)), {"max_words": 1, "fill_gaps": 0.35})
    assert [(c.start, c.end) for c in result.cues] == [(0.0, 0.4), (0.4, 0.6), (2.0, 2.2)]


def test_pop_style_on_defaults():
    config = load_config()
    ws = words(
        *[
            (w, i * 0.3, i * 0.3 + 0.25)
            for i, w in enumerate(["e", "hoje", "eu", "trouxe", "a", "bolsa"])
        ]
    )
    result = make_cues(transcript(segment(ws)), config["styles"]["pop"], "pop")
    assert texts(result) == ["e hoje", "eu trouxe", "a bolsa"]
    assert all(len(c.text.split()) <= 2 for c in result.cues)
