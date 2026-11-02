"""Asking for the access password in a terminal (`flosub serve`, `flosub auth set`).

The launcher has its own window for the same job. Both go through `access.Access`, so the rules
(length, the common-password list, hashing) are the same. Input and output are injected so the
dialogue can be tested.
"""

from __future__ import annotations

import getpass
from collections.abc import Callable

from legendaria_engine import access
from legendaria_engine.i18n import t


def error_text(code: str) -> str:
    """The translated reason a password was refused."""
    return t(f"password.error.{code}", min=access.MIN_LENGTH, max=access.MAX_LENGTH)


def set_password_interactively(
    settings: access.Access,
    secret: Callable[[str], str] = getpass.getpass,
    out: Callable[[str], None] = print,
    tries: int = 3,
) -> bool:
    """Ask for a password (empty answer: generate one) and save it. True when one was saved."""
    for _ in range(tries):
        typed = secret(t("password.prompt"))
        generated = not typed
        password = access.generate_password() if generated else typed
        if not generated:
            problem = access.check_password(password)
            if problem:
                out(error_text(problem))
                continue
            if secret(t("password.confirm")) != password:
                out(t("password.mismatch"))
                continue
        settings.set_password(password)
        if generated:
            out(t("password.generated", password=password))
        out(t("password.saved"))
        return True
    return False


def offer_password(
    settings: access.Access,
    ask: Callable[[str], str] = input,
    secret: Callable[[str], str] = getpass.getpass,
    out: Callable[[str], None] = print,
) -> bool:
    """When no password is set, explain it and ask whether to set one now (every time, until it is)."""
    if settings.has_password:
        return True
    out(t("password.intro"))
    answer = ask(t("password.ask")).strip().lower()
    if answer and answer[0] not in ("y", "s"):  # yes / sim; Enter means yes
        out(t("password.skipped"))
        return False
    return set_password_interactively(settings, secret, out)
