# SPDX-License-Identifier: GPL-3.0-or-later
"""Find and run the `flosub` engine as a separate process (ADR-003). No bpy here.

Events arrive as JSON lines on stdout; a background thread reads them into a queue
so Blender's UI never waits on the process.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

APP_NAME = "legendaria"
EXE = "flosub.exe" if sys.platform == "win32" else "flosub"


def user_data_dir() -> Path:
    """Same per-OS data folder the engine uses (platformdirs, appauthor=False)."""
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_NAME


def user_config_dir() -> Path:
    """Same per-OS config folder the engine uses (platformdirs, appauthor=False)."""
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def managed_engine() -> Path:
    """Where the add-on's "Install engine" step (stage 2b) puts flosub."""
    venv = user_data_dir() / "engine" / "venv"
    return venv / ("Scripts" if sys.platform == "win32" else "bin") / EXE


def candidate_paths() -> list[Path]:
    """Usual per-user install locations that Blender's PATH may not include."""
    home = Path.home()
    paths = [managed_engine(), home / ".local" / "bin" / EXE]
    if sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        paths += sorted(appdata.glob(f"Python/Python3*/Scripts/{EXE}"))
    elif sys.platform == "darwin":
        paths += sorted(home.glob(f"Library/Python/3.*/bin/{EXE}"))
    return paths


def find_engine(custom: str = "") -> Path | None:
    """The flosub executable: custom path (file or folder), managed install, PATH, user dirs."""
    if custom:
        path = Path(custom).expanduser()
        if path.is_dir():
            path = path / EXE
        return path if path.is_file() else None
    managed = managed_engine()
    if managed.is_file():
        return managed
    found = shutil.which("flosub")
    if found:
        return Path(found)
    return next((p for p in candidate_paths() if p.is_file()), None)


def version_key(text: str) -> tuple:
    """Sortable key for versions like "0.1.0", "0.1.0.dev1" or "flosub 0.2.0" (dev < final)."""
    number = text.split()[-1] if text.split() else "0"
    main, _, dev = number.partition(".dev")
    parts = tuple(int(p) if p.isdigit() else 0 for p in main.split("."))
    return (*parts, int(dev) if dev.isdigit() else -1) if dev else (*parts, 10**9)


def _popen_kwargs() -> dict:
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def run_json(engine: Path, args: list[str], timeout: float = 60) -> dict:
    """Run a quick command that prints one JSON document (e.g. `models list --json`)."""
    result = subprocess.run([str(engine), *args], timeout=timeout, check=False, **_popen_kwargs())
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"flosub exited with code {result.returncode}")
    return json.loads(result.stdout)


def run_text(engine: Path, args: list[str], timeout: float = 30) -> str:
    """Run a quick command and return its stdout (e.g. `--version`)."""
    result = subprocess.run([str(engine), *args], timeout=timeout, check=False, **_popen_kwargs())
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"flosub exited with code {result.returncode}")
    return result.stdout.strip()


class EngineJob:
    """A running `flosub --progress json ...` process whose events can be polled."""

    def __init__(self, engine: Path, args: list[str]) -> None:
        self.events: queue.Queue[dict] = queue.Queue()
        self._stderr: list[str] = []
        self.process = subprocess.Popen(
            [str(engine), "--progress", "json", *args], **_popen_kwargs()
        )
        self._out_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._out_thread.start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        for line in self.process.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                self.events.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    def _read_stderr(self) -> None:
        for line in self.process.stderr:
            self._stderr.append(line.rstrip())
            del self._stderr[:-50]  # keep the tail only

    def poll(self) -> list[dict]:
        """Events received since the last call (never blocks)."""
        out = []
        while True:
            try:
                out.append(self.events.get_nowait())
            except queue.Empty:
                return out

    @property
    def finished(self) -> bool:
        """True once the process has exited and all of its output has been read."""
        return self.process.poll() is not None and not self._out_thread.is_alive()

    @property
    def returncode(self) -> int | None:
        """Exit code, or None while running."""
        return self.process.poll()

    def stderr_tail(self) -> str:
        """Last lines the engine wrote to stderr (for error reports)."""
        return "\n".join(self._stderr[-10:])

    def cancel(self) -> None:
        """Stop the engine: terminate, then kill if it does not exit quickly.

        On Windows `flosub.exe` is a launcher that starts Python as a child process, so
        the whole process tree is ended; otherwise the transcription would keep running.
        """
        if self.finished:
            return
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                check=False,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def wait(self, timeout: float | None = None) -> int:
        """Block until the process exits and its output is read (tests and scripts, not the UI)."""
        code = self.process.wait(timeout=timeout)
        self._out_thread.join(timeout=5)
        return code
