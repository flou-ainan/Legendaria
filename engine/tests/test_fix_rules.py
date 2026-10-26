from legendaria_engine.review import fix_rules
from legendaria_engine.review.align import retime
from legendaria_engine.review.glossary import Glossary
from legendaria_engine.review.suggestions import Review, apply
from legendaria_engine.schema import Segment, Transcript, Word


def make(words):
    ws = [Word(s, e, w, p) for w, s, e, p in words]
    seg = Segment(ws[0].start, ws[-1].end, " ".join(w.word.strip() for w in ws), ws)
    return Transcript("a.mp4", "pt", 10.0, "small", "cpu", [seg])


def glossary(text):
    g = Glossary()
    g.merge_text(text)
    return g


T = make(
    [
        (" Eu", 0.0, 0.2, 0.9),
        (" me", 0.2, 0.3, 0.9),
        (" chamo", 0.3, 0.6, 0.9),
        (" Mariana", 0.6, 1.0, 0.8),
        (" Nakley.", 1.0, 1.5, 0.22),
        (" Fio", 1.6, 1.8, 0.9),
        (" de", 1.8, 1.9, 0.9),
        (" polieste.", 1.9, 2.5, 0.44),
    ]
)


def test_explicit_fix_keeps_trailing_punctuation():
    found = fix_rules.suggest(T, glossary("Nakley -> Enacles\n"))
    assert [(s.before, s.after, s.reason) for s in found] == [
        ("Nakley.", "Enacles.", "glossary fix")
    ]


def test_multiword_fix():
    found = fix_rules.suggest(T, glossary("Mariana Nakley -> Mariana Enacles\n"))
    assert [(s.first, s.last, s.after) for s in found] == [(3, 5, "Mariana Enacles.")]


def test_fuzzy_match_on_uncertain_word():
    found = fix_rules.suggest(T, glossary("Poliéster\n"))
    assert [(s.before, s.after) for s in found] == [("polieste.", "Poliéster.")]
    assert "Poliéster" in found[0].reason


def test_fuzzy_ignores_confident_words():
    confident = make([(" polieste", 0.0, 0.5, 0.95)])
    assert fix_rules.suggest(confident, glossary("Poliéster\n")) == []


def test_short_words_need_a_closer_match():
    t = make([(" Bet", 0.0, 0.3, 0.3), (" bom", 0.3, 0.6, 0.3)])
    found = fix_rules.suggest(t, glossary("Beth\nbem\n"))
    assert [s.after for s in found] == ["Beth"]  # "bom"/"bem" is 0.67, below the short-word limit


def test_retime_spreads_over_the_old_span():
    old = [Word(1.0, 1.4, " bolsa", 0.5), Word(1.4, 1.8, " Bet", 0.3)]
    new = retime(old, "bolsa Beth")
    assert [w.word for w in new] == [" bolsa", " Beth"]
    assert new[0].start == 1.0 and new[-1].end == 1.8 and new[0].end == new[1].start
    assert all(w.probability == 1.0 for w in new)


def test_apply_and_round_trip(tmp_path):
    g = glossary("Nakley -> Enacles\nPoliéster\n")
    found = fix_rules.suggest(T, g)
    fixed = apply(T, found)
    assert fixed.segments[0].text == "Eu me chamo Mariana Enacles. Fio de Poliéster."
    assert T.segments[0].text != fixed.segments[0].text  # original untouched
    review = Review(transcript="a.json", suggestions=found)
    review.save(tmp_path / "a.review.json")
    assert Review.load(tmp_path / "a.review.json") == review


def test_keeps_a_capital_first_letter():
    assert fix_rules.match_case("Bolsa Bet", "bolsa Beth") == "Bolsa Beth"
    assert fix_rules.match_case("bolsa", "Beth") == "Beth"
    t = make([(" Bolsa", 0.0, 0.3, 0.3), (" Bet,", 0.3, 0.6, 0.3)])
    assert [s.after for s in fix_rules.suggest(t, glossary("bolsa Beth\n"))] == ["Bolsa Beth,"]
