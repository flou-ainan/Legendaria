# SPDX-License-Identifier: GPL-3.0-or-later
"""Exact preview (plan 04 §10): the captions rendered by libass, shown above the strips.

The text strips stay the place to edit. "Exact preview" sends them to `flosub overlay`, which
renders the final look (font, colors, pop) to a transparent `.mov`; the movie goes above the
captions with Alpha Over and the captions channel is muted. Rendering the scene then gives the
burned-in video. After edits, run it again; "Remove exact preview" brings the strips back.
"""

from __future__ import annotations

import time
from pathlib import Path

import bpy

from . import compat, engine_bridge, strips
from .i18n import tr
from .operators import cache_dir, engine_or_error, redraw_sequencer, render_size

TIMER_INTERVAL = 0.2
OVERLAY_TAG = "legendaria_overlay"  # custom property on the overlay movie strip


def overlay_strips(editor) -> list:
    """The exact-preview movie strips in the editor."""
    return [s for s in compat.top_strips(editor) if OVERLAY_TAG in s]


def free_channel_above(editor, channel: int, start: int, end: int) -> int:
    """First channel above `channel` with nothing between `start` and `end`."""
    for candidate in range(channel + 1, 129):
        if not any(
            s.channel == candidate and s.frame_final_start < end and s.frame_final_end > start
            for s in compat.top_strips(editor)
        ):
            return candidate
    raise ValueError(tr("No free channel for the preview."))


def caption_channel(context) -> int:
    """The captions channel: the one used last, else the setting."""
    settings = context.scene.legendaria
    return settings.last_channel or settings.channel


def remove_overlay(context) -> int:
    """Delete the preview movie(s), unmute the captions channel; returns how many were removed."""
    editor = context.scene.sequence_editor
    if editor is None:
        return 0
    old = overlay_strips(editor)
    files = {Path(bpy.path.abspath(compat.media_path(s))) for s in old}
    for strip in old:
        compat.remove_strip(editor, strip)
    for path in files:  # each render has its own file, so Blender never shows stale frames
        if path.name.endswith(".overlay.mov"):
            path.unlink(missing_ok=True)
    channel = caption_channel(context)
    if channel and hasattr(editor, "channels"):
        editor.channels[channel].mute = False
    return len(old)


def place_overlay(context, movie: Path, channel: int):
    """Put the rendered `.mov` above the captions with Alpha Over and mute the captions."""
    scene = context.scene
    editor = scene.sequence_editor
    remove_overlay(context)
    target = free_channel_above(editor, channel, scene.frame_start, scene.frame_end + 1)
    strip = compat.top_strips(editor).new_movie(
        "LGD exact preview", str(movie), target, scene.frame_start
    )
    strip.blend_type = "ALPHA_OVER"
    strip[OVERLAY_TAG] = 1
    if hasattr(editor, "channels"):
        editor.channels[channel].mute = True
    return strip


class LEGENDARIA_OT_exact_preview(bpy.types.Operator):
    """Show the captions exactly as the final video will look (font, colors, pop animation). Run it again after editing"""

    bl_idname = "legendaria.exact_preview"
    bl_label = "Exact preview"

    _timer = None
    _job = None
    _movie = None
    _error = ""
    _channel = 0

    @classmethod
    def poll(cls, context):
        """Needs captions and no running job."""
        settings = context.scene.legendaria
        return (
            bool(context.scene.sequence_editor)
            and caption_channel(context) > 0
            and not settings.running
        )

    def execute(self, context):
        """Write the strips as cues and start `flosub overlay` in the background."""
        scene = context.scene
        settings = scene.legendaria
        self._channel = caption_channel(context)
        cues = strips.read_cues(scene, scene.sequence_editor, self._channel)
        if not cues:
            self.report(
                {"ERROR"}, tr("No text strips on channel {channel}.").format(channel=self._channel)
            )
            return {"CANCELLED"}
        folder = cache_dir()
        source = strips.write_cues_file(folder / "preview.cues.json", cues, settings.style, "")
        fps = strips.scene_fps(scene)
        duration = (scene.frame_end + 1 - scene.frame_start) / fps
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self._movie = folder / f"{bpy.path.clean_name(scene.name)}-{stamp}.overlay.mov"
        args = ["overlay", str(source), "--style", settings.style, "--size", render_size(scene)]
        args += [
            "--fps",
            f"{fps:.6g}",
            "--duration",
            f"{duration:.3f}",
            "--output",
            str(self._movie),
        ]
        try:
            self._job = engine_bridge.EngineJob(engine_or_error(), args)
        except (ValueError, OSError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings.running, settings.cancel_requested = True, False
        settings.progress, settings.status = 0.0, tr("Rendering the exact preview…")
        self._error = ""
        wm = context.window_manager
        self._timer = wm.event_timer_add(TIMER_INTERVAL, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        """Follow the render; place the movie when it is done."""
        settings = context.scene.legendaria
        if event.type == "ESC" or settings.cancel_requested:
            self._job.cancel()
            self._finish(context)
            settings.status = tr("Cancelled.")
            return {"CANCELLED"}
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        for e in self._job.poll():
            kind = e.get("event")
            if kind == "progress" and e.get("total"):
                settings.progress = min(1.0, e["t"] / e["total"])
            elif kind == "error":
                self._error = e.get("message", "")
        redraw_sequencer(context)
        if not self._job.finished:
            return {"PASS_THROUGH"}
        self._finish(context)
        if self._job.returncode != 0 or not self._movie.is_file():
            settings.status = tr("Failed.")
            self.report(
                {"ERROR"}, self._error or self._job.stderr_tail() or tr("The engine failed.")
            )
            return {"CANCELLED"}
        try:
            place_overlay(context, self._movie, self._channel)
        except (ValueError, RuntimeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings.status = tr(
            "Exact preview ready. The caption strips are muted; run it again after editing."
        )
        self.report({"INFO"}, settings.status)
        return {"FINISHED"}

    def _finish(self, context) -> None:
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.scene.legendaria.running = False
        redraw_sequencer(context)


class LEGENDARIA_OT_remove_preview(bpy.types.Operator):
    """Remove the exact preview and show the editable caption strips again"""

    bl_idname = "legendaria.remove_preview"
    bl_label = "Remove exact preview"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Delete the overlay movie and unmute the captions."""
        remove_overlay(context)
        context.scene.legendaria.status = ""
        redraw_sequencer(context)
        return {"FINISHED"}


CLASSES = (LEGENDARIA_OT_exact_preview, LEGENDARIA_OT_remove_preview)


def register() -> None:
    """Register the preview operators."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Remove them."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
