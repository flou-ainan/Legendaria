"""`flosub serve`: the local web editor's backend (plan 07, ADR-014).

Standard library only (`http.server`). It serves the built Svelte app, the video (HTTP Range,
so the browser can seek), the project file, `.ass` for the live preview, and runs
transcription and export as jobs whose events stream over Server-Sent Events.

It listens on 127.0.0.1 only and rejects requests whose Host or Origin is not local, so a
web page on the internet cannot drive it (DNS rebinding, cross-site requests).
"""

from __future__ import annotations

import json
import mimetypes
import re
import shutil
import subprocess
import sys
import threading
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from legendaria_engine import fonts, formats, media, workspace
from legendaria_engine.ass import to_ass, with_look
from legendaria_engine.config import load_config
from legendaria_engine.cues import CueList
from legendaria_engine.events import Reporter
from legendaria_engine.project import Project, ProjectError, project_path

WEB_DIR = Path(__file__).parent / "web"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
# Routes that work before a video is open (everything else answers 409).
NO_VIDEO_ROUTES = {
    "/api/state", "/api/browse", "/api/open", "/api/upload",
    "/api/glossary", "/api/glossary/export", "/api/glossary/add", "/api/glossary/import",
    "/api/glossary/use",
}  # fmt: skip
# COOP/COEP make the page cross-origin isolated, so JASSUB can use worker threads.
ISOLATION = {
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Resource-Policy": "same-origin",
}
CHUNK = 1 << 20
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("text/javascript", ".js")


class Job(Reporter):
    """A background task (transcribe, export) that records its events for SSE readers."""

    def __init__(self, kind: str) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.events: list[dict[str, Any]] = []
        self.finished = False
        self._changed = threading.Condition()

    def emit(self, event: str, **data: Any) -> None:
        """Record one event and wake the SSE readers."""
        with self._changed:
            self.events.append({"event": event, **data})
            if event in ("done", "error"):
                self.finished = True
            self._changed.notify_all()

    def wait(self, seen: int, timeout: float = 15.0) -> list[dict[str, Any]]:
        """Events after the first `seen` ones; blocks up to `timeout` for new ones."""
        with self._changed:
            if len(self.events) <= seen and not self.finished:
                self._changed.wait(timeout)
            return self.events[seen:]


class Session:
    """One video being edited: its project file, config and running jobs."""

    def __init__(self, video: Path, config: dict[str, Any]) -> None:
        self.video = video
        self.config = config
        self.project_file = project_path(video)
        self.info = media.probe(video, config)
        self.jobs: dict[str, Job] = {}
        self._peaks: dict[str, Any] | None = None
        self.lock = threading.Lock()

    def project(self) -> Project | None:
        """The saved project, or None before the first transcription."""
        return Project.load(self.project_file) if self.project_file.is_file() else None

    def state(self) -> dict[str, Any]:
        """Everything the editor needs on load."""
        project = self.project()
        base = with_look(self.look(project.style if project else self.config["style"]), None)
        return {
            "video": self.video.name,
            "path": str(self.video),
            "font": (project.look.get("font") if project else None) or base["font"],
            "fonts": fonts.catalog(),
            "base": {"font": base["font"], "y": base["position"][1]},
            "media": self.info,
            "project": project.to_dict() if project else None,
            **workspace.options(self.config),
        }

    def peaks(self) -> dict[str, Any]:
        """Waveform peaks (100 per second), computed once per session."""
        with self.lock:
            if self._peaks is None:
                values = media.peaks(self.config, self.video)
                if not values:  # no audio: a flat line the length of the video
                    values = [0.0] * round(self.info["duration"] * 100)
                self._peaks = {"per_sec": 100, "duration": self.info["duration"], "peaks": values}
            return self._peaks

    def review(self) -> list[dict[str, Any]]:
        """Glossary suggestions (layer 2, no AI) for the saved cues, as the editor shows them.

        Each cue is a segment. Its words are used when they still match its text; after a manual
        edit the text is split into words with full confidence, so only explicit fixes apply.
        """
        from legendaria_engine.review import fix_rules, glossary
        from legendaria_engine.schema import Segment, Transcript, Word

        project = self.project()
        if project is None:
            raise ProjectError("Nothing to review yet: transcribe first.")
        segments = []
        for cue in project.cues:
            words = cue.words
            if " ".join("".join(w.word for w in words).split()) != cue.text:
                words = [Word(cue.start, cue.end, f" {token}") for token in cue.text.split()]
            segments.append(Segment(cue.start, cue.end, cue.text, words))
        transcript = Transcript(
            self.video.name, project.language, project.duration, "", "", segments
        )
        rules = self.config["review"]
        found = fix_rules.suggest(
            transcript,
            glossary.load([], media=self.video),
            threshold=rules.get("fuzzy_threshold", 0.82),
            low_confidence=rules.get("low_confidence", 0.5),
        )
        return [
            {
                "id": f.id,
                "cue": f.segment,
                "start": f.start,
                "before": f.before,
                "after": f.after,
                "reason": f.reason,
            }
            for f in found
        ]

    def look(self, style: str) -> dict[str, Any]:
        """The style's `.ass` look from the config (empty if unknown)."""
        return self.config["styles"].get(style, {}).get("ass", {})

    def size(self) -> tuple[int, int] | None:
        """The video's (width, height) for the `.ass` canvas."""
        return (self.info["width"], self.info["height"]) if self.info["width"] else None

    def ass_text(self, cues: CueList, style: str, override: dict[str, Any] | None = None) -> str:
        """`.ass` for these cues in the style's look (plus the project's `look` overrides), on the video's canvas."""
        rules = self.config["styles"].get(style) or self.config["styles"][self.config["style"]]
        look = with_look(rules.get("ass"), override)
        return to_ass(cues, look, self.size(), rules.get("line_length"))

    def start(self, kind: str, work) -> Job:
        """Run `work(job)` in a thread; only one job at a time."""
        with self.lock:
            if any(not j.finished for j in self.jobs.values()):
                raise RuntimeError("Another task is still running.")
            job = Job(kind)
            self.jobs[job.id] = job

        def run() -> None:
            try:
                work(job)
            except Exception as exc:  # report every failure to the browser
                job.error(str(exc) or type(exc).__name__)

        threading.Thread(target=run, daemon=True).start()
        return job

    def transcribe(self, job: Job, options: dict[str, Any]) -> None:
        """Run `flosub transcribe` in a child process (it may re-exec for CUDA), relay events."""
        style = options.get("style") or self.config["style"]
        command = [
            sys.executable,
            "-m",
            "legendaria_engine",
            "--progress",
            "json",
            "transcribe",
            str(self.video),
            "--format",
            "json,cues",
            "--style",
            style,
        ]
        for key in ("model", "language"):
            if options.get(key):
                command += [f"--{key}", str(options[key])]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
        )
        failed = None
        for line in process.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = event.pop("event", "log")
            if name == "error":
                failed = event.get("message", "")
            elif name != "done":
                job.emit(name, **event)
        process.wait()
        if failed is not None or process.returncode != 0:
            job.error(failed or f"Transcription failed (exit code {process.returncode}).")
            return
        cues_file = self.video.parent / f"{self.video.stem}.cues.json"
        cues = CueList.from_dict(json.loads(cues_file.read_text(encoding="utf-8")))
        previous = (
            self.project()
        )  # generating again keeps the cuts and the look, only the cues are new
        project = Project.new(self.video, self.info["duration"], cues)
        if previous is not None:
            project.keep, project.look = previous.keep, previous.look
        project.save(self.project_file)
        job.emit("done", project=project.to_dict())

    def export(self, job: Job, fmt: str) -> None:
        """Write the edited video (`mp4`) or subtitles (`srt`, `vtt`, `ass`) next to the source."""
        project = self.project()
        if project is None:
            raise ProjectError("Nothing to export yet: transcribe first.")
        edited = project.edited_cues()
        target = self.video.parent / f"{self.video.stem}.edited.{fmt}"
        rules = self.config["styles"].get(project.style, {})
        if fmt == "mp4":
            if target.resolve() == self.video.resolve():
                raise media.MediaError("The output would overwrite the input video.")
            media.render(
                self.config,
                self.video,
                project.keep,
                self.ass_text(edited, project.style, project.look),
                target,
                job,
            )
        elif fmt == "ass":
            target.write_text(self.ass_text(edited, project.style, project.look), encoding="utf-8")
        elif fmt in formats.WRITERS:
            text = formats.WRITERS[fmt](edited, rules.get("line_length"))
            target.write_text(text, encoding="utf-8")
        else:
            raise ValueError(f"Unknown export format: {fmt}")
        job.emit("done", outputs=[str(target)])


def find_font(name: str, bold: bool) -> Path | None:
    """The font file the system uses for `name` (fontconfig), so the preview matches FFmpeg."""
    tool = shutil.which("fc-match")
    if not tool:
        return None
    pattern = f"{name}:bold" if bold else name
    result = subprocess.run(
        [tool, "-f", "%{file}", pattern], capture_output=True, text=True, check=False
    )
    path = Path(result.stdout.strip()) if result.returncode == 0 else None
    return path if path and path.is_file() else None


class Handler(BaseHTTPRequestHandler):
    """Routes for the editor. `self.server.session` is the open video."""

    server_version = "Legendaria"
    protocol_version = "HTTP/1.1"

    @property
    def session(self) -> Session:
        """The open video's session (routes that need one are guarded by `_ready`)."""
        return self.server.session  # type: ignore[attr-defined]

    def _ready(self, path: str) -> bool:
        """False (after answering 409) when the route needs a video and none is open."""
        if self.session is None and path.startswith("/api/") and path not in NO_VIDEO_ROUTES:
            self._error(HTTPStatus.CONFLICT, "Open a video first.")
            return False
        return True

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet: only errors are printed."""

    # --- helpers -------------------------------------------------------------

    def _local(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        origin = self.headers.get("Origin")
        origin_host = urlsplit(origin).hostname if origin else None
        return host in LOCAL_HOSTS and (origin is None or origin_host in LOCAL_HOSTS)

    def _send(self, status: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in {**ISOLATION, **(extra or {})}.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"null")

    # --- routes --------------------------------------------------------------

    def do_GET(self) -> None:
        """Static app, state, media, font, preview `.ass` and job events."""
        if not self._local():
            return self._error(HTTPStatus.FORBIDDEN, "Only local requests are allowed.")
        url = urlsplit(self.path)
        path, query = url.path, parse_qs(url.query)
        if not self._ready(path):
            return None
        try:
            if path == "/api/state":
                if self.session is None:
                    return self._json({"video": None, **workspace.options(self.server.config)})
                return self._json(self.session.state())
            if path == "/api/browse":
                return self._json(workspace.browse((query.get("path") or [None])[0]))
            if path == "/api/glossary":
                return self._json(workspace.glossary_state())
            if path == "/api/glossary/export":
                name = (query.get("name") or [workspace.glossary_state()["active"]])[0]
                text = workspace.glossary_text(name).encode("utf-8")
                return self._send(
                    200, text, "text/plain; charset=utf-8",
                    {"Content-Disposition": f'attachment; filename="{name}.txt"'},
                )  # fmt: skip
            if path == "/api/media":
                return self._file(self.session.video)
            if path == "/api/review":
                return self._json({"suggestions": self.session.review()})
            if path == "/api/peaks":
                return self._json(self.session.peaks())
            if path == "/api/font":
                return self._font()
            if match := re.fullmatch(r"/api/fonts/([\w.-]+\.ttf)", path):
                bundled = fonts.FONTS_DIR / match.group(1)
                if match.group(1) not in {e["file"] for e in fonts.catalog()}:
                    return self._error(HTTPStatus.NOT_FOUND, "Unknown font.")
                return self._file(bundled)
            if path == "/api/preview.ass":
                project = self.session.project()
                if project is None:
                    return self._error(HTTPStatus.NOT_FOUND, "No project yet.")
                text = self.session.ass_text(project.cue_list(), project.style, project.look)
                return self._send(200, text.encode("utf-8"), "text/plain; charset=utf-8")
            if match := re.fullmatch(r"/api/jobs/(\w+)/events", path):
                return self._events(match.group(1))
            return self._static(path)
        except (ProjectError, ValueError, OSError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))

    do_HEAD = do_GET

    def do_PUT(self) -> None:
        """Save the project (validated and normalized); returns what was saved."""
        if not self._local():
            return self._error(HTTPStatus.FORBIDDEN, "Only local requests are allowed.")
        if urlsplit(self.path).path != "/api/project":
            return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        if not self._ready("/api/project"):
            return None
        try:
            project = Project.from_dict(self._body())
        except (ProjectError, json.JSONDecodeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        project.save(self.session.project_file)
        self._json(project.to_dict())

    def do_POST(self) -> None:
        """Start a job: `/api/transcribe` {model, language, style} or `/api/export` {format}."""
        if not self._local():
            return self._error(HTTPStatus.FORBIDDEN, "Only local requests are allowed.")
        url = urlsplit(self.path)
        path = url.path
        if not self._ready(path):
            return None
        try:
            if path == "/api/upload":
                name = Path((parse_qs(url.query).get("name") or ["video"])[0]).name or "video"
                return self._upload(name)
            options = self._body() or {}
            if path == "/api/open":
                return self._open(Path(str(options.get("path", ""))).expanduser())
            if path == "/api/glossary/add":
                return self._json({"added": workspace.glossary_add(str(options.get("entry", "")))})
            if path == "/api/glossary/import":
                name = workspace.glossary_import(
                    str(options.get("name", "")), str(options.get("text", ""))
                )
                return self._json({"name": name, **workspace.glossary_state()})
            if path == "/api/glossary/use":
                workspace.glossary_use(str(options.get("name", "")))
                return self._json(workspace.glossary_state())
            if path == "/api/transcribe":
                job = self.session.start(
                    "transcribe", lambda j: self.session.transcribe(j, options)
                )
            elif path == "/api/export":
                fmt = str(options.get("format", ""))
                job = self.session.start("export", lambda j: self.session.export(j, fmt))
            else:
                return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        except RuntimeError as exc:
            return self._error(HTTPStatus.CONFLICT, str(exc))
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        return self._json({"job": job.id})

    def _open(self, video: Path) -> None:
        """Open `video` as the session (a project file next to it is loaded if it exists).

        A path to the project file itself (`<video>.legendaria.json`) opens its video.
        """
        if video.name.endswith(workspace.PROJECT_SUFFIX):
            video = video.with_name(video.name.removesuffix(workspace.PROJECT_SUFFIX))
        if not video.is_file():
            return self._error(HTTPStatus.BAD_REQUEST, f"File not found: {video}")
        try:
            self.server.session = Session(video.resolve(), self.server.config)  # type: ignore[attr-defined]
        except media.MediaError as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        return self._json(self.session.state())

    def _upload(self, name: str) -> None:
        """Store a dropped file in the uploads folder (streamed) and open it."""
        length = int(self.headers.get("Content-Length") or 0)
        folder = workspace.uploads_dir() / uuid.uuid4().hex[:8]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / name
        with target.open("wb") as handle:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(CHUNK, remaining))
                if not chunk:
                    break
                handle.write(chunk)
                remaining -= len(chunk)
        return self._open(target)

    def _events(self, job_id: str) -> None:
        job = self.session.jobs.get(job_id)
        if job is None:
            return self._error(HTTPStatus.NOT_FOUND, "Unknown job.")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        for key, value in ISOLATION.items():
            self.send_header(key, value)
        self.end_headers()
        self.close_connection = True
        seen = 0
        try:
            while True:
                fresh = job.wait(seen)
                for event in fresh:
                    self.wfile.write(f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode())
                seen += len(fresh)
                if not fresh:
                    self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
                if job.finished and seen >= len(job.events):
                    return
        except (BrokenPipeError, ConnectionResetError):
            return

    def _font(self) -> None:
        project = self.session.project()
        look = self.session.look(project.style if project else self.session.config["style"])
        family = (project.look.get("font") if project else None) or look.get("font", "Arial")
        font = fonts.file_for(family) or find_font(family, look.get("bold", True))
        if font is None:
            return self._error(
                HTTPStatus.NOT_FOUND, "Font not found (the preview uses a fallback)."
            )
        return self._file(font)

    def _static(self, path: str) -> None:
        root = WEB_DIR.resolve()
        target = (root / path.lstrip("/")).resolve()
        if path in ("", "/") or not target.is_file():
            target = root / "index.html"
        if not target.is_relative_to(root) or not target.is_file():
            message = "The editor is not built. Run `npm run build` in web/ (see CONTRIBUTING.md)."
            return self._error(HTTPStatus.NOT_FOUND, message)
        return self._file(target)

    def _file(self, path: Path) -> None:
        """Send a file, honoring a single `Range: bytes=a-b` (video seeking)."""
        size = path.stat().st_size
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        start, end, status = 0, size - 1, 200
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", "").strip())
        if match and size:
            first, last = match.groups()
            if first:
                start, end = int(first), min(int(last), size - 1) if last else size - 1
            elif last:
                start = max(0, size - int(last))
            if start > end:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = 206
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        for key, value in ISOLATION.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with path.open("rb") as handle:
                handle.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = handle.read(min(CHUNK, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser cancels range requests while seeking


def make_server(
    video: Path | None = None, port: int = 0, config: dict[str, Any] | None = None
) -> ThreadingHTTPServer:
    """A server on 127.0.0.1 (`port` 0 picks a free one), with `video` open if given."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.config = config or load_config()  # type: ignore[attr-defined]
    server.session = Session(video, server.config) if video else None  # type: ignore[attr-defined]
    return server


def serve(video: Path | None, port: int, open_browser: bool, reporter: Reporter) -> None:
    """Run the editor until Ctrl+C (the browser asks for a video when none is given)."""
    server = make_server(video, port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    reporter.emit("serving", url=url, video=str(video) if video else None)
    reporter.log(f"Editor running at {url} (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.server_close()
