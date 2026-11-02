import socket
import urllib.request

import pytest

from legendaria_engine import launcher
from legendaria_engine.access import Access


@pytest.fixture
def settings(tmp_path):
    return Access(tmp_path / "access.json")


def test_the_guide_has_a_copy_per_language():
    assert launcher.docs_url("en").endswith("/docs/network-access.md")
    assert launcher.docs_url("pt-BR").endswith("/docs/network-access.pt-BR.md")
    assert launcher.docs_url("fr").endswith("/docs/network-access.md"), "no French copy: English"


def test_the_form_checks_the_password_and_the_repeat():
    assert launcher.check_form("battery staple", "battery staple") is None
    assert "8" in launcher.check_form("short", "short", "en")
    assert (
        launcher.check_form("battery staple", "battery stapl", "pt-BR")
        == "As duas senhas são diferentes."
    )
    assert (
        launcher.check_form("password", "password", "en") == "That password is too easy to guess."
    )


def test_the_editor_starts_local_only_without_a_password(settings):
    running = launcher.start_editor(settings, port=0)
    try:
        assert running.network == [] and running.server.server_address[0] == "127.0.0.1"
        assert urllib.request.urlopen(running.url + "api/access", timeout=5).status == 200
    finally:
        running.stop()


def test_the_editor_listens_on_the_network_with_a_password(settings):
    settings.set_password("battery staple")
    running = launcher.start_editor(settings, port=0)
    try:
        assert running.server.server_address[0] == "0.0.0.0"
        assert all(url.endswith(f":{running.port}/") for url in running.network)
    finally:
        running.stop()


def test_a_taken_port_moves_on_to_the_next(settings):
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]
        running = launcher.start_editor(settings, port=port, tries=20)
        try:
            assert running.port != port
        finally:
            running.stop()


def test_every_port_taken_is_an_error(settings):
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        with pytest.raises(OSError):
            launcher.start_editor(settings, port=taken.getsockname()[1], tries=1)


# --- the window: needs tkinter and a display (CI has none; `xvfb-run pytest` runs them) ---------


@pytest.fixture
def window(settings, monkeypatch):
    tk = pytest.importorskip("tkinter")
    opened = []
    monkeypatch.setattr(launcher.webbrowser, "open", opened.append)
    monkeypatch.setattr(launcher, "SPLASH_MS", 1)
    try:
        shown = launcher.Window(settings, "en")
    except tk.TclError:
        pytest.skip("no display")
    shown.opened = opened
    # a dialog that never closes would block `wait_window` for ever: close it so the test fails instead of hanging
    shown.root.after(
        15000,
        lambda: [w.destroy() for w in shown.root.winfo_children() if w.winfo_class() == "Toplevel"],
    )
    yield shown
    shown.stop()
    shown.root.destroy()


def walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from walk(child)


def press(root, text, kind="TButton"):
    for widget in walk(root):
        if widget.winfo_class() == kind and str(widget.cget("text")) == text:
            widget.invoke()
            return
    raise AssertionError(f"no {kind} {text!r}")


def fill(root, values):
    entries = [w for w in walk(root) if w.winfo_class() == "TEntry"]
    for entry, value in zip(entries, values, strict=True):
        entry.delete(0, "end")
        entry.insert(0, value)


def dialog_of(window):
    return next(w for w in window.root.winfo_children() if w.winfo_class() == "Toplevel")


def test_window_without_a_password_says_so(window):
    assert "Only this computer" in window.status.get()
    assert window.stop_button.instate(["disabled"])
    assert window.password_button.cget("text") == "Set the password…"


def test_first_run_asks_for_the_password_and_saves_it(window):
    """Open the editor with no password: the dialog appears; a good password is stored and the editor is on the network."""
    window.root.after(
        200,
        lambda: (
            fill(dialog_of(window), ["battery staple", "battery staple"]),
            press(dialog_of(window), "Save"),
        ),
    )
    window.open_editor()
    window.root.update()
    assert window.settings.has_password and window.settings.verify("battery staple")
    assert window.running is not None and window.running.server.server_address[0] == "0.0.0.0"
    assert window.opened == [window.running.url]
    assert not window.stop_button.instate(["disabled"])


def test_not_now_starts_local_only_and_asks_again_next_time(window):
    window.root.after(200, lambda: press(dialog_of(window), "Not now"))
    window.open_editor()
    window.root.update()
    assert not window.settings.has_password
    assert window.running is not None and window.running.network == []
    window.stop()
    window.root.after(200, lambda: press(dialog_of(window), "Not now"))
    window.open_editor()  # asked again, because there is still no password
    window.root.update()
    assert window.running is not None


def test_a_bad_password_keeps_the_dialog_open_with_the_reason(window):
    seen = {}

    def try_short():
        fill(dialog_of(window), ["short", "short"])
        press(dialog_of(window), "Save")
        seen["texts"] = [
            str(w.cget("text")) for w in walk(dialog_of(window)) if w.winfo_class() == "TLabel"
        ]
        seen["still_open"] = dialog_of(window).winfo_exists()
        press(dialog_of(window), "Not now")

    window.root.after(200, try_short)
    window.ask_password()
    assert seen["still_open"] and not window.settings.has_password


def test_generate_fills_both_fields_with_a_valid_password(window):
    def generate_and_save():
        press(dialog_of(window), "Generate for me")
        press(dialog_of(window), "Save")

    window.root.after(200, generate_and_save)
    window.ask_password()
    assert window.settings.has_password


def test_changing_the_password_while_running_restarts_on_the_network(window):
    window.root.after(200, lambda: press(dialog_of(window), "Not now"))
    window.open_editor()
    port = window.running.port
    assert window.running.server.server_address[0] == "127.0.0.1"
    window.root.after(
        200,
        lambda: (
            fill(dialog_of(window), ["battery staple", "battery staple"]),
            press(dialog_of(window), "Save"),
        ),
    )
    window.ask_password()
    assert window.running.server.server_address[0] == "0.0.0.0" and window.running.port == port


def test_the_info_balloon_links_to_the_guide(window):
    window.show_info()
    link = next(
        w
        for w in walk(window.root)
        if w.winfo_class() == "Label" and "Tailscale" in str(w.cget("text"))
    )
    window.root.update()  # the balloon must be on screen to get the click
    link.event_generate("<Button-1>", x=2, y=2)
    window.root.update()
    assert window.opened[-1] == launcher.docs_url("en")


def test_fallback_to_the_terminal_without_a_window(monkeypatch, capsys):
    monkeypatch.setattr(
        launcher, "Window", lambda: (_ for _ in ()).throw(RuntimeError("no display"))
    )
    called = []
    monkeypatch.setattr(launcher, "run_in_terminal", lambda: called.append(1) or 0)
    assert launcher.main() == 0 and called
    assert "tkinter" in capsys.readouterr().err
