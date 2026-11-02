import json
from pathlib import Path

import pytest

from legendaria_engine import access, access_prompt, cli, i18n
from legendaria_engine.access import Access

LOCALES = Path(i18n.__file__).parent / "locales"


@pytest.fixture
def settings(tmp_path):
    return Access(tmp_path / "access.json")


def dialogue(*typed):
    """A `secret` function that answers with `typed` in order, and the lines shown."""
    answers, shown = iter(typed), []
    return (lambda prompt: next(answers)), shown, shown.append


def test_typing_a_password_asks_twice_and_saves(settings):
    secret, shown, out = dialogue("battery staple", "battery staple")
    assert access_prompt.set_password_interactively(settings, secret, out)
    assert settings.verify("battery staple") and shown[-1] == i18n.t("password.saved", "en")


def test_enter_generates_one_and_shows_it_once(settings):
    secret, shown, out = dialogue("")
    assert access_prompt.set_password_interactively(settings, secret, out)
    password = (
        next(line for line in shown if "Your password is" in line).split(": ")[1].split("\n")[0]
    )
    assert settings.verify(password) and access.check_password(password) is None


def test_a_weak_or_mismatched_password_asks_again_then_gives_up(settings):
    secret, shown, out = dialogue(
        "short", "battery staple", "different one", "password", "123456789", "x"
    )
    assert not access_prompt.set_password_interactively(settings, secret, out)
    assert not settings.has_password and len(shown) == 3


def test_the_offer_is_made_until_a_password_exists(settings):
    secret, shown, out = dialogue()
    assert not access_prompt.offer_password(settings, lambda prompt: "n", secret, out)
    assert not settings.has_password and shown[-1] == i18n.t("password.skipped", "en")
    secret, shown, out = dialogue("battery staple", "battery staple")
    assert access_prompt.offer_password(settings, lambda prompt: "", secret, out), "Enter means yes"
    assert access_prompt.offer_password(settings, lambda prompt: 1 / 0, secret, out), (
        "nothing to ask now"
    )


def test_auth_cli(capsys):
    assert cli.main(["auth", "status"]) == 0
    assert "No password" in capsys.readouterr().out
    assert cli.main(["auth", "set", "--generate"]) == 0
    out = capsys.readouterr().out
    assert "Your password is" in out and Access().has_password
    assert cli.main(["auth", "status"]) == 0 and "A password is set" in capsys.readouterr().out
    assert cli.main(["auth", "reset"]) == 0 and not Access().has_password


def test_auth_set_without_a_terminal_refuses(capsys):
    assert cli.main(["auth", "set"]) == 2


def test_every_language_has_every_key():
    source = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    codes = i18n.available()
    assert "en" in codes and "pt-BR" in codes
    for code in codes:
        data = json.loads((LOCALES / f"{code}.json").read_text(encoding="utf-8"))
        assert "_name" in data, code
        if code == "pt-BR":  # always complete; other languages may be partial (English fills in)
            assert set(data) == set(source), set(data) ^ set(source)
        for key, text in data.items():
            if key in source:
                assert sorted(_fields(text)) == sorted(_fields(source[key])), (code, key)


def _fields(text):
    import string

    return [name for _, name, *_ in string.Formatter().parse(text) if name]


def test_language_choice(monkeypatch):
    monkeypatch.delenv("LEGENDARIA_LANG", raising=False)
    assert i18n.language("pt_BR.UTF-8") == "pt-BR"
    assert i18n.language("pt") == "pt-BR" and i18n.language("pt-PT") == "pt-BR"
    assert i18n.language("en_US.UTF-8") == "en" and i18n.language("fr") == "en"
    monkeypatch.setenv("LEGENDARIA_LANG", "pt-BR")
    assert i18n.language() == "pt-BR"
    assert i18n.t("password.error.too_short", "pt-BR", min=8) == "Use pelo menos 8 caracteres."
    assert i18n.t("no.such.key", "pt-BR") == "no.such.key"
