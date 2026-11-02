"""The launcher: a small window that starts the editor and opens the browser (ADR-026, plan 12).

Run it with the `legendaria` command. The first time (and every time, until a password is set)
it offers to set the access password, because that is what lets a phone on the same Wi-Fi, or
Tailscale, open the editor safely. An (i) button explains why and links to the guide.

The logic (`start_editor`, `check_form`, `docs_url`) has no window in it, so it can be tested
without a display. Without tkinter, or without a display, it falls back to the terminal.
"""

from __future__ import annotations

import sys
import threading
import webbrowser
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from typing import Any

from legendaria_engine import access, i18n
from legendaria_engine.i18n import t

DOCS = "https://github.com/flou-ainan/Legendaria/blob/main/docs/network-access{}.md"
DOCS_LANGUAGES = {
    "pt-BR"
}  # languages that have their own copy of the guide; the others read English
DEFAULT_PORT = 8765
PORT_TRIES = 10  # if 8765 is taken, try the next ones
SPLASH_MS = 700  # long enough to read, so the window does not just flash


def docs_url(lang: str) -> str:
    """The network guide in `lang` (English when there is no copy in that language)."""
    return DOCS.format(f".{lang}" if lang in DOCS_LANGUAGES else "")


def check_form(password: str, repeat: str, lang: str | None = None) -> str | None:
    """None when the two fields make a good password, else the translated reason they do not."""
    problem = access.check_password(password)
    if problem:
        return t(f"password.error.{problem}", lang, min=access.MIN_LENGTH, max=access.MAX_LENGTH)
    return None if password == repeat else t("password.mismatch", lang)


@dataclass
class Running:
    """The editor server running in this process."""

    server: ThreadingHTTPServer
    thread: threading.Thread
    url: str
    network: list[str]

    @property
    def port(self) -> int:
        """The port it listens on."""
        return self.server.server_address[1]

    def stop(self) -> None:
        """Stop serving and free the port."""
        self.server.shutdown()
        self.server.server_close()


def start_editor(
    settings: access.Access, port: int = DEFAULT_PORT, tries: int = PORT_TRIES
) -> Running:
    """Start the editor in a thread, on the first free port from `port`."""
    from legendaria_engine.server import make_server, network_urls

    failure: OSError | None = None
    for offset in range(tries):
        try:
            server = make_server(settings=settings, port=port + offset if port else 0)
            break
        except OSError as exc:  # the port is taken: try the next one
            failure = exc
    else:
        raise failure or OSError("No free port.")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    return Running(server, thread, url, network_urls(server))


def run_in_terminal() -> int:
    """No window available: do what `flosub serve` does, asking for the password in the terminal."""
    from legendaria_engine import access_prompt
    from legendaria_engine.events import make_reporter
    from legendaria_engine.server import serve

    settings = access.Access()
    if sys.stdin.isatty() and sys.stdout.isatty():
        access_prompt.offer_password(settings)
    reporter = make_reporter("auto")
    try:
        serve(None, DEFAULT_PORT, True, reporter, (), settings)
    except KeyboardInterrupt:
        pass
    finally:
        reporter.close()
    return 0


class Window:
    """The launcher window (tkinter)."""

    def __init__(self, settings: access.Access | None = None, lang: str | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk = tk, ttk
        self.settings = settings or access.Access()
        self.lang = i18n.language(lang)
        self.running: Running | None = None
        self.root = tk.Tk()
        self.root.title(self.tr("launcher.title"))
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        frame = ttk.Frame(self.root, padding=20)
        frame.grid()
        ttk.Label(frame, text=self.tr("launcher.title"), font=("TkDefaultFont", 20, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(frame, text="ⓘ", width=3, command=self.show_info).grid(
            row=0, column=1, sticky="e"
        )
        self.status = tk.StringVar()
        ttk.Label(frame, textvariable=self.status, wraplength=380, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(10, 10)
        )
        self.address = tk.StringVar()
        ttk.Entry(frame, textvariable=self.address, state="readonly", width=44).grid(
            row=2, column=0, columnspan=2, sticky="we"
        )
        self.open_button = ttk.Button(frame, command=self.open_editor)
        self.open_button.grid(row=3, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.password_button = ttk.Button(frame, command=self.ask_password)
        self.password_button.grid(row=4, column=0, columnspan=2, sticky="we", pady=(6, 0))
        self.stop_button = ttk.Button(frame, command=self.stop)
        self.stop_button.grid(row=5, column=0, columnspan=2, sticky="we", pady=(6, 0))
        self.refresh()

    def tr(self, key: str, **values: Any) -> str:
        """A text in the window's language."""
        return t(key, self.lang, **values)

    def refresh(self) -> None:
        """Show what is true now: running or not, where a phone can open it, what the buttons do."""
        has = self.settings.has_password
        self.open_button.config(text=self.tr("launcher.open"))
        self.password_button.config(
            text=self.tr("launcher.change_password" if has else "launcher.set_password")
        )
        self.stop_button.config(text=self.tr("launcher.stop"))
        if self.running is None:
            self.status.set(self.tr("launcher.local_only" if not has else "password.status.set"))
            self.address.set("")
            self.stop_button.state(["disabled"])
        else:
            lines = [self.tr("launcher.running")]
            if self.running.network:
                lines.append(self.tr("launcher.network", address=self.running.network[0]))
                self.address.set(self.running.network[0])
            else:
                lines.append(self.tr("launcher.local_only"))
                self.address.set(self.running.url)
            self.status.set("\n".join(lines))
            self.stop_button.state(["!disabled"])

    # --- actions ---------------------------------------------------------------

    def open_editor(self) -> None:
        """Ask for the password if there is none, start the editor if needed, open the browser."""
        if self.running is None:
            if not self.settings.has_password:
                self.ask_password()  # every time, until one is set; "Not now" starts local-only
            self.splash(self.start)
        else:
            webbrowser.open(self.running.url)

    def start(self) -> None:
        """Start the server and open the browser."""
        try:
            self.running = start_editor(self.settings)
        except OSError as exc:
            from tkinter import messagebox

            messagebox.showerror(self.tr("launcher.title"), self.tr("launcher.error", error=exc))
            return
        webbrowser.open(self.running.url)
        self.refresh()

    def restart(self) -> None:
        """Start the editor again on the same port (after the password changed, it may listen on the network now)."""
        port = self.running.port if self.running else DEFAULT_PORT
        self.stop()
        try:
            self.running = start_editor(self.settings, port, tries=1)
        except OSError as exc:
            from tkinter import messagebox

            messagebox.showerror(self.tr("launcher.title"), self.tr("launcher.error", error=exc))

    def stop(self) -> None:
        """Stop the editor; the window stays."""
        if self.running is not None:
            self.running.stop()
            self.running = None
        self.refresh()

    def quit(self) -> None:
        """Stop the editor and close the window."""
        self.stop()
        self.root.destroy()

    def splash(self, then: Any) -> None:
        """A borderless window with the name and "Starting…" while `then` runs (shown at least a moment)."""
        tk, ttk = self.tk, self.ttk
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        box = ttk.Frame(window, padding=40, relief="solid")
        box.grid()
        ttk.Label(box, text=self.tr("launcher.title"), font=("TkDefaultFont", 28, "bold")).grid()
        ttk.Label(box, text=self.tr("launcher.starting")).grid(pady=(8, 0))
        window.update_idletasks()
        x = self.root.winfo_screenwidth() // 2 - window.winfo_reqwidth() // 2
        y = self.root.winfo_screenheight() // 2 - window.winfo_reqheight() // 2
        window.geometry(f"+{x}+{y}")
        window.update()
        then()
        self.root.after(SPLASH_MS, window.destroy)

    def show_info(self) -> None:
        """The (i) balloon: what the password is for, and a link to the guide."""
        tk, ttk = self.tk, self.ttk
        box = tk.Toplevel(self.root)
        box.title(self.tr("launcher.info.title"))
        box.transient(self.root)
        frame = ttk.Frame(box, padding=16)
        frame.grid()
        ttk.Label(frame, text=self.tr("launcher.info.text"), wraplength=380, justify="left").grid()
        link = tk.Label(
            frame,
            text=self.tr("launcher.info.link"),
            fg="#1a5fb4",
            cursor="hand2",
            font=("TkDefaultFont", 10, "underline"),
        )
        link.grid(sticky="w", pady=(10, 0))
        link.bind("<Button-1>", lambda _event: webbrowser.open(docs_url(self.lang)))

    def ask_password(self) -> None:
        """The dialog to set or change the password. It returns when it is closed."""
        tk, ttk = self.tk, self.ttk
        dialog = tk.Toplevel(self.root)
        dialog.title(self.tr("launcher.password.title"))
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=16)
        frame.grid()
        ttk.Label(frame, text=self.tr("password.intro"), wraplength=340, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Button(frame, text="ⓘ", width=3, command=self.show_info).grid(row=0, column=2)
        first, second = tk.StringVar(), tk.StringVar()
        shown = tk.BooleanVar(value=False)
        ttk.Label(frame, text=self.tr("launcher.password.new")).grid(row=1, column=0, sticky="w")
        entry_a = ttk.Entry(frame, textvariable=first, show="•", width=26)
        entry_a.grid(row=1, column=1, pady=4)
        ttk.Label(frame, text=self.tr("launcher.password.repeat")).grid(row=2, column=0, sticky="w")
        entry_b = ttk.Entry(frame, textvariable=second, show="•", width=26)
        entry_b.grid(row=2, column=1, pady=4)
        message = tk.StringVar()
        ttk.Label(frame, textvariable=message, wraplength=380, justify="left").grid(
            row=4, column=0, columnspan=3, sticky="w"
        )

        def show_hide() -> None:
            mark = "" if shown.get() else "•"
            entry_a.config(show=mark)
            entry_b.config(show=mark)

        def generate() -> None:
            password = access.generate_password()
            first.set(password)
            second.set(password)
            shown.set(True)
            show_hide()
            message.set(self.tr("launcher.password.generated", password=password))

        def save() -> None:
            problem = check_form(first.get(), second.get(), self.lang)
            if problem:
                message.set(problem)
                return
            self.settings.set_password(first.get())
            dialog.destroy()
            if (
                self.running is not None
            ):  # it listened on this computer only: restart on the network
                self.restart()
            self.refresh()

        ttk.Checkbutton(
            frame, text=self.tr("launcher.password.show"), variable=shown, command=show_hide
        ).grid(row=3, column=1, sticky="w")
        ttk.Button(frame, text=self.tr("launcher.password.generate"), command=generate).grid(
            row=3, column=0, sticky="w"
        )
        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text=self.tr("launcher.password.later"), command=dialog.destroy).grid(
            row=0, column=0, padx=6
        )
        ttk.Button(buttons, text=self.tr("launcher.password.save"), command=save).grid(
            row=0, column=1
        )
        entry_a.focus_set()
        dialog.grab_set()
        self.root.wait_window(dialog)


def main() -> int:
    """The `legendaria` command: the launcher window, or the terminal when there is none."""
    try:
        window = Window()
    except Exception as exc:  # no tkinter, or no display (a server, SSH): the terminal still works
        print(t("launcher.no_tk"), f"({type(exc).__name__}: {exc})", file=sys.stderr)
        return run_in_terminal()
    window.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
