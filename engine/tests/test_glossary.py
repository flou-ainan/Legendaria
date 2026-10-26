import pytest

from legendaria_engine.review import glossary
from legendaria_engine.review.bias import hotwords
from legendaria_engine.review.glossary import Glossary, fold

TEXT = """# Names
Mariana Enacles
bolsa Beth
Poliéster
polieste -> Poliéster
Nakley → Enacles
"""


def test_parse_terms_fixes_and_comments():
    g = Glossary()
    g.merge_text(TEXT)
    assert g.terms == ["Mariana Enacles", "bolsa Beth", "Poliéster", "Enacles"]
    assert g.fixes == {"polieste": "Poliéster", "nakley": "Enacles"}


def test_fold_ignores_case_accents_and_edge_punctuation():
    assert fold("“Poliéster”…") == "poliester"
    assert fold("¿Olá!") == "ola"


def test_load_merges_global_project_and_extra(tmp_path):
    glossary.global_file().parent.mkdir(parents=True, exist_ok=True)
    glossary.global_file().write_text("crochê\n", encoding="utf-8")
    media = tmp_path / "video.mp4"
    glossary.project_file(media).write_text("Beth\n", encoding="utf-8")
    extra = tmp_path / "more.txt"
    extra.write_text("x -> Xis\n", encoding="utf-8")
    g = glossary.load([extra], media=media)
    assert g.terms == ["crochê", "Beth", "Xis"]
    assert len(g.sources) == 3


def test_missing_explicit_file_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        glossary.load([tmp_path / "nope.txt"])


def test_add_entry_creates_dedupes_and_keeps_comments(tmp_path):
    path = tmp_path / "g.txt"
    assert glossary.add_entry(path, "Poliéster") is True
    assert glossary.add_entry(path, "poliester") is False  # same term ignoring accents/case
    assert glossary.add_entry(path, "polieste -> Poliéster") is True
    assert glossary.add_entry(path, "polieste -> Poliéster") is False
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Legendária glossary")
    assert text.endswith("Poliéster\npolieste -> Poliéster\n")


def test_hotwords_respect_budget():
    g = Glossary(terms=["alpha", "beta", "gamma"])
    assert hotwords(g) == "alpha, beta, gamma"
    assert hotwords(g, max_chars=12) == "alpha, beta"
    assert hotwords(Glossary()) is None
