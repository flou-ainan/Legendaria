# SPDX-License-Identifier: GPL-3.0-or-later
"""Operators: generate (runs the engine without blocking), cancel, re-apply style, export, refresh."""

from __future__ import annotations

import tempfile
from pathlib import Path

import bpy

from . import compat, engine_bridge, properties, strips, timecode
from .i18n import tr

TIMER_INTERVAL = 0.2


def cache_dir() -> Path:
    """Where transcripts and cues are saved: `//legendaria/` next to the .blend, else a temp folder."""
    if bpy.data.filepath:
        return Path(bpy.path.abspath("//")) / "legendaria"
    return Path(tempfile.gettempdir()) / "legendaria"


def redraw_sequencer(context) -> None:
    """Refresh sequencer areas so progress shows up."""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "SEQUENCE_EDITOR":
                area.tag_redraw()


class Plan:
    """What a generate / re-apply run will do; built and validated before anything starts."""

    def __init__(self, context, require_media_file: bool = True, media_name: str = ""):
        scene = context.scene
        self.settings = scene.legendaria
        self.editor = scene.sequence_editor
        if self.editor is None:
            raise ValueError(tr("Add a video to the Video Sequencer first."))
        by_name = compat.all_strips(self.editor).get(media_name) if media_name else None
        media = by_name or self.editor.active_strip
        if media is None or media.type not in {"MOVIE", "SOUND"}:
            raise ValueError(tr("Select a video or audio strip first."))
        self.media = media
        self.media_file = compat.media_path(media)
        if require_media_file and not Path(self.media_file).is_file():
            raise ValueError(tr("Media file not found: {path}").format(path=self.media_file))
        _, self.frame_start, self.frame_end = strips.media_range(media)
        self.channel = self.settings.channel or strips.pick_channel(
            self.editor, media, self.frame_start, self.frame_end
        )
        if strips.foreign_in_range(self.editor, self.channel, self.frame_start, self.frame_end):
            raise ValueError(
                tr("Channel {channel} has other strips here. Choose another channel.").format(
                    channel=self.channel
                )
            )
        self.replaced = len(
            strips.tagged_in_range(self.editor, self.channel, self.frame_start, self.frame_end)
        )

    def confirm_message(self) -> str:
        """Warning shown before replacing captions (owner requirement R3)."""
        return tr(
            "{count} captions on channel {channel} will be replaced. Your edits to them will be lost."
        ).format(count=self.replaced, channel=self.channel)


def engine_or_error() -> Path:
    """The detected engine, refreshing the cache once if needed."""
    if properties.ENGINE["path"] is None:
        properties.refresh_engine_info()
    engine = properties.ENGINE["path"]
    if engine is None:
        raise ValueError(tr("Transcription engine not found. See the add-on preferences."))
    return engine


def finish_strips(context, plan: Plan, cues_path: Path, style: str) -> int:
    """Create the caption strips from a cues file and remember where they came from."""
    data = strips.load_cues(cues_path)
    created = strips.create_strips(
        context.scene, plan.editor, data["cues"], plan.media, plan.channel, style
    )
    plan.settings.media_strip = plan.media.name
    plan.settings.last_channel = plan.channel
    return len(created)


class LEGENDARIA_OT_generate(bpy.types.Operator):
    """Transcribe the selected strip and create caption strips"""

    bl_idname = "legendaria.generate"
    bl_label = "Generate subtitles"
    bl_options = {"REGISTER"}

    _timer = None
    _job = None
    _plan = None
    _cues = None
    _error = ""

    @classmethod
    def poll(cls, context):
        """Needs a scene with settings and no job already running."""
        return context.scene is not None and not context.scene.legendaria.running

    def invoke(self, context, event):
        """Validate, then ask before replacing existing captions."""
        try:
            plan = Plan(context)
            engine_or_error()
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        if plan.replaced:
            return context.window_manager.invoke_confirm(
                self,
                event,
                title=tr("Replace captions?"),
                message=plan.confirm_message(),
                confirm_text=tr("Replace"),
                icon="WARNING",
            )
        return self.execute(context)

    def execute(self, context):
        """Start the engine and the modal timer."""
        try:
            self._plan = Plan(context)
            engine = engine_or_error()
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings = self._plan.settings
        out_dir = cache_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        args = ["transcribe", self._plan.media_file, "--model", settings.model]
        args += ["--language", settings.language, "--style", settings.style]
        args += ["--format", "json,cues", "--output-dir", str(out_dir)]
        try:
            self._job = engine_bridge.EngineJob(engine, args)
        except OSError as exc:
            self.report({"ERROR"}, tr("Could not start the engine: {error}").format(error=exc))
            return {"CANCELLED"}
        settings.running, settings.cancel_requested = True, False
        settings.progress, settings.status = 0.0, tr("Starting…")
        self._cues, self._error = None, ""
        wm = context.window_manager
        self._timer = wm.event_timer_add(TIMER_INTERVAL, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def handle_event(self, event: dict) -> None:
        """Update progress and status from one engine event."""
        settings = self._plan.settings
        kind = event.get("event")
        if kind == "model_download":
            if event.get("finished"):
                settings.status = tr("Model downloaded. Loading…")
            else:
                total = event.get("total") or 0
                settings.progress = event.get("downloaded", 0) / total if total else 0.0
                settings.status = tr("Downloading model {model}… {pct}%").format(
                    model=event.get("model", ""), pct=round(settings.progress * 100)
                )
        elif kind == "start":
            settings.progress = 0.0
            settings.status = tr("Transcribing on {device}…").format(device=event.get("device", ""))
        elif kind == "progress" and event.get("total"):
            settings.progress = min(1.0, event["t"] / event["total"])
            settings.status = tr("Transcribing… {pct}%").format(pct=round(settings.progress * 100))
        elif kind == "warning":
            self.report({"WARNING"}, event.get("message", ""))
        elif kind == "error":
            self._error = event.get("message", "")
        elif kind == "done":
            self._cues = next(
                (Path(p) for p in event.get("outputs", []) if p.endswith(".cues.json")), None
            )
            transcript = next(
                (
                    Path(p)
                    for p in event.get("outputs", [])
                    if p.endswith(".json") and not p.endswith(".cues.json")
                ),
                None,
            )
            if transcript:
                settings.transcript_path = str(transcript)

    def modal(self, context, event):
        """Poll the engine on each timer tick; Esc or the Cancel button stops it."""
        settings = self._plan.settings
        if event.type == "ESC" or settings.cancel_requested:
            self._job.cancel()
            self.cleanup(context)
            settings.status = tr("Cancelled.")
            self.report({"WARNING"}, tr("Cancelled."))
            return {"CANCELLED"}
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        for engine_event in self._job.poll():
            self.handle_event(engine_event)
        redraw_sequencer(context)
        if not self._job.finished:
            return {"PASS_THROUGH"}
        for engine_event in self._job.poll():  # anything left after exit
            self.handle_event(engine_event)
        self.cleanup(context)
        if self._job.returncode != 0 or self._cues is None:
            message = self._error or self._job.stderr_tail() or tr("The engine failed.")
            settings.status = tr("Failed.")
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        try:
            count = finish_strips(context, self._plan, self._cues, settings.style)
        except (OSError, ValueError, KeyError) as exc:
            settings.status = tr("Failed.")
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings.progress = 1.0
        settings.status = tr("{count} captions created on channel {channel}.").format(
            count=count, channel=self._plan.channel
        )
        self.report({"INFO"}, settings.status)
        return {"FINISHED"}

    def cleanup(self, context) -> None:
        """Remove the timer and mark the job as stopped."""
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        self._plan.settings.running = False
        self._plan.settings.cancel_requested = False
        redraw_sequencer(context)


class LEGENDARIA_OT_cancel(bpy.types.Operator):
    """Stop the running transcription"""

    bl_idname = "legendaria.cancel"
    bl_label = "Cancel"

    def execute(self, context):
        """Ask the running generate operator to stop."""
        context.scene.legendaria.cancel_requested = True
        return {"FINISHED"}


class LEGENDARIA_OT_reapply_style(bpy.types.Operator):
    """Rebuild the captions from the saved transcript with the chosen style, without transcribing again"""

    bl_idname = "legendaria.reapply_style"
    bl_label = "Re-apply style"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Needs a saved transcript and no running job."""
        settings = context.scene.legendaria
        return bool(settings.transcript_path) and not settings.running

    def invoke(self, context, event):
        """Ask before replacing captions."""
        try:
            plan = Plan(context, False, context.scene.legendaria.media_strip)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        if plan.replaced:
            return context.window_manager.invoke_confirm(
                self,
                event,
                title=tr("Replace captions?"),
                message=plan.confirm_message(),
                confirm_text=tr("Replace"),
                icon="WARNING",
            )
        return self.execute(context)

    def execute(self, context):
        """Run `flosub export --style` on the saved transcript and rebuild the strips."""
        try:
            plan = Plan(context, False, context.scene.legendaria.media_strip)
            engine = engine_or_error()
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        transcript = Path(plan.settings.transcript_path)
        if not transcript.is_file():
            self.report({"ERROR"}, tr("Saved transcript not found. Generate the subtitles again."))
            return {"CANCELLED"}
        stem = transcript.parent / transcript.name.removesuffix(".json")
        job = engine_bridge.EngineJob(
            engine,
            [
                "export",
                str(transcript),
                "--style",
                plan.settings.style,
                "--format",
                "cues",
                "--output",
                str(stem),
            ],
        )
        job.wait(timeout=60)
        events = job.poll()
        done = next((e for e in events if e.get("event") == "done"), None)
        if job.returncode != 0 or done is None:
            error = next((e.get("message") for e in events if e.get("event") == "error"), "")
            self.report({"ERROR"}, error or job.stderr_tail() or tr("The engine failed."))
            return {"CANCELLED"}
        count = finish_strips(context, plan, Path(done["outputs"][0]), plan.settings.style)
        self.report(
            {"INFO"},
            tr("{count} captions created on channel {channel}.").format(
                count=count, channel=plan.channel
            ),
        )
        return {"FINISHED"}


class LEGENDARIA_OT_export(bpy.types.Operator):
    """Save the captions on the channel as an SRT or VTT file (with your edits)"""

    bl_idname = "legendaria.export"
    bl_label = "Export subtitles"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.srt;*.vtt", options={"HIDDEN"})
    file_format: bpy.props.EnumProperty(
        name="Format",
        items=[
            ("srt", "SRT", "SubRip (YouTube, most players)"),
            ("vtt", "VTT", "WebVTT (web players)"),
        ],
    )

    def export_channel(self, context) -> int:
        """Channel to export: the one used last, else the setting, else the active strip's."""
        settings = context.scene.legendaria
        active = context.scene.sequence_editor and context.scene.sequence_editor.active_strip
        return settings.last_channel or settings.channel or (active.channel if active else 1)

    def invoke(self, context, event):
        """Open the file browser with a sensible default name."""
        base = (
            Path(bpy.data.filepath).with_suffix("")
            if bpy.data.filepath
            else Path.home() / "subtitles"
        )
        self.filepath = str(base) + f".{self.file_format}"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        """Write the file from the text strips."""
        editor = context.scene.sequence_editor
        if editor is None:
            self.report({"ERROR"}, tr("Add a video to the Video Sequencer first."))
            return {"CANCELLED"}
        channel = self.export_channel(context)
        cues = strips.read_cues(context.scene, editor, channel)
        if not cues:
            self.report(
                {"ERROR"}, tr("No text strips on channel {channel}.").format(channel=channel)
            )
            return {"CANCELLED"}
        path = Path(bpy.path.abspath(self.filepath))
        if path.suffix.lower() != f".{self.file_format}":
            path = path.with_name(path.name + f".{self.file_format}")
        writer = timecode.to_vtt if self.file_format == "vtt" else timecode.to_srt
        path.write_text(writer(cues), encoding="utf-8")
        self.report(
            {"INFO"}, tr("Saved {count} subtitles to {path}").format(count=len(cues), path=path)
        )
        return {"FINISHED"}


class LEGENDARIA_OT_refresh_engine(bpy.types.Operator):
    """Look for the transcription engine again and reload its models"""

    bl_idname = "legendaria.refresh_engine"
    bl_label = "Refresh engine"

    def execute(self, context):
        """Re-run engine detection."""
        if properties.refresh_engine_info(context):
            self.report({"INFO"}, properties.ENGINE["version"])
        else:
            self.report({"WARNING"}, properties.ENGINE["error"])
        return {"FINISHED"}


CLASSES = (
    LEGENDARIA_OT_generate,
    LEGENDARIA_OT_cancel,
    LEGENDARIA_OT_reapply_style,
    LEGENDARIA_OT_export,
    LEGENDARIA_OT_refresh_engine,
)


def register() -> None:
    """Register the operators."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Remove the operators."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
