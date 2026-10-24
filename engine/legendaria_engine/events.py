"""Progress reporting: JSON lines for programs (the Blender add-on), a progress bar for humans.

Every JSON event is one object per line on stdout with an `event` key:
`start`, `progress`, `model_download`, `log`, `warning`, `done`, `error`.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO


class Reporter:
    """Base reporter. Subclasses decide how events are shown."""

    def emit(self, event: str, **data: Any) -> None:
        """Send one event."""
        raise NotImplementedError

    def progress(self, current: float, total: float) -> None:
        """Transcription progress in seconds of media."""
        self.emit("progress", t=round(current, 2), total=round(total, 2))

    def log(self, message: str) -> None:
        """Informational message."""
        self.emit("log", message=message)

    def warning(self, message: str) -> None:
        """Non-fatal problem (e.g. GPU fallback)."""
        self.emit("warning", message=message)

    def error(self, message: str) -> None:
        """Fatal problem; the command exits with a non-zero code."""
        self.emit("error", message=message)

    def close(self) -> None:
        """Release any resource (e.g. a progress bar)."""


class JsonReporter(Reporter):
    """Machine-readable events, one JSON object per line."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout

    def emit(self, event: str, **data: Any) -> None:
        """Write the event as one JSON line and flush, so readers see it at once."""
        self.stream.write(json.dumps({"event": event, **data}, ensure_ascii=False) + "\n")
        self.stream.flush()


class HumanReporter(Reporter):
    """Readable output on stderr, with a tqdm bar for transcription progress."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stderr
        self._bar = None
        self._last = 0.0

    def emit(self, event: str, **data: Any) -> None:
        """Render the event as text: progress bar, messages, saved files."""
        if event == "progress":
            self._progress(data["t"], data["total"])
        elif event == "model_download":
            if data.get("finished"):
                self.stream.write(f"\rDownloading model {data.get('model', '')}: done   \n")
            else:
                done, total = data.get("downloaded", 0), data.get("total") or 0
                pct = f"{100 * done / total:.0f}%" if total else f"{done / 1e6:.0f} MB"
                self.stream.write(f"\rDownloading model {data.get('model', '')}: {pct}   ")
            self.stream.flush()
        elif event in ("log", "warning", "error"):
            self._close_bar()
            prefix = {"log": "", "warning": "Warning: ", "error": "Error: "}[event]
            self.stream.write(f"{prefix}{data.get('message', '')}\n")
        elif event == "done":
            self._close_bar()
            for path in data.get("outputs", []):
                self.stream.write(f"Saved: {path}\n")
        elif event == "start":
            self.stream.write(
                f"Model {data.get('model')} on {data.get('device')} ({data.get('compute_type')}), "
                f"language: {data.get('language') or 'auto'}\n"
            )

    def _progress(self, current: float, total: float) -> None:
        from tqdm import tqdm

        if self._bar is None:
            self._bar = tqdm(total=round(total), unit="s", desc="Transcribing", file=self.stream)
        step = round(current) - round(self._last)
        if step > 0:
            self._bar.update(step)
        self._last = current

    def _close_bar(self) -> None:
        if self._bar is not None:
            self._bar.close()
            self._bar = None

    def close(self) -> None:
        """Close the progress bar, if any."""
        self._close_bar()


def make_reporter(mode: str = "auto") -> Reporter:
    """`json`, `human`, or `auto` (human when stdout is a terminal, JSON otherwise)."""
    if mode == "auto":
        mode = "human" if sys.stdout.isatty() else "json"
    return HumanReporter() if mode == "human" else JsonReporter()
