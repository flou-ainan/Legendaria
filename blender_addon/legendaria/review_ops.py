# SPDX-License-Identifier: GPL-3.0-or-later
"""Glossary and review operators (plan 03, stage 3c): thin wrappers around the engine.

All logic stays in `flosub glossary …` and `flosub review …` (ADR-011); these operators
only call them and show the results.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import bpy

from . import engine_bridge, properties, strips, timecode
from .i18n import tr
from .operators import Plan, engine_or_error, redraw_sequencer, use_exact_colors

TIMER_INTERVAL = 0.2
EDGE_PUNCT = " .,;:!?\u2026\"'\u201c\u201d\u2018\u2019()[]"


def _engine_call(op, args: list[str]) -> list[dict] | None:
    """Run a quick engine command; report errors on the operator and return None."""
    try:
        return engine_bridge.run_events(engine_or_error(), args)
    except (ValueError, RuntimeError, OSError) as exc:
        op.report({"ERROR"}, str(exc))
        return None


def _clean_term(text: str) -> str:
    """Caption text → a glossary term: one line, no surrounding punctuation."""
    return re.sub(r"\s+", " ", text).strip(EDGE_PUNCT)


class LEGENDARIA_OT_glossary_new(bpy.types.Operator):
    """Create a new, empty glossary and make it the active one"""

    bl_idname = "legendaria.glossary_new"
    bl_label = "New glossary"

    name: bpy.props.StringProperty(name="Name", default="")

    def invoke(self, context, event):
        """Ask for the name."""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """`flosub glossary new NAME --activate`."""
        if not self.name.strip():
            self.report({"ERROR"}, tr("Type a name for the glossary."))
            return {"CANCELLED"}
        if _engine_call(self, ["glossary", "new", self.name.strip(), "--activate"]) is None:
            return {"CANCELLED"}
        properties.refresh_glossaries()
        redraw_sequencer(context)
        return {"FINISHED"}


class LEGENDARIA_OT_glossary_import(bpy.types.Operator):
    """Add a glossary file (.txt) to your glossaries and make it the active one"""

    bl_idname = "legendaria.glossary_import"
    bl_label = "Import glossary"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.txt", options={"HIDDEN"})

    def invoke(self, context, event):
        """Open the file browser."""
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        """`flosub glossary import FILE`, then `use` it."""
        events = _engine_call(self, ["glossary", "import", bpy.path.abspath(self.filepath)])
        if events is None:
            return {"CANCELLED"}
        name = events[-1].get("name", "")
        if name and _engine_call(self, ["glossary", "use", name]) is None:
            return {"CANCELLED"}
        properties.refresh_glossaries()
        self.report({"INFO"}, tr("Glossary '{name}' imported.").format(name=name))
        return {"FINISHED"}


class LEGENDARIA_OT_glossary_export(bpy.types.Operator):
    """Save the active glossary to a file, to share it or keep a copy"""

    bl_idname = "legendaria.glossary_export"
    bl_label = "Export glossary"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.txt", options={"HIDDEN"})

    def invoke(self, context, event):
        """Open the file browser with the glossary's name."""
        self.filepath = str(Path.home() / f"{properties.GLOSSARY['active']}.txt")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        """`flosub glossary export NAME --to FILE`."""
        path = bpy.path.abspath(self.filepath)
        if not path.lower().endswith(".txt"):
            path += ".txt"
        name = properties.GLOSSARY["active"]
        if _engine_call(self, ["glossary", "export", name, "--to", path]) is None:
            return {"CANCELLED"}
        self.report({"INFO"}, tr("Glossary saved to {path}").format(path=path))
        return {"FINISHED"}


class LEGENDARIA_OT_glossary_edit(bpy.types.Operator):
    """Open the active glossary in your text editor (one term per line, or 'wrong -> right')"""

    bl_idname = "legendaria.glossary_edit"
    bl_label = "Edit glossary"

    def execute(self, context):
        """Create the file if needed and open it with the system's editor."""
        name = properties.GLOSSARY["active"]
        path = Path(properties.GLOSSARY["folder"]) / f"{name}.txt"
        if not path.is_file() and _engine_call(self, ["glossary", "new", name]) is None:
            return {"CANCELLED"}
        if not path.is_file():
            self.report({"ERROR"}, tr("Glossary file not found: {path}").format(path=path))
            return {"CANCELLED"}
        bpy.ops.wm.path_open(filepath=str(path))
        return {"FINISHED"}


class LEGENDARIA_OT_glossary_add(bpy.types.Operator):
    """Add a word or name to a glossary, so the next transcriptions and reviews get it right"""

    bl_idname = "legendaria.glossary_add"
    bl_label = "Add to glossary"
    bl_options = {"REGISTER"}

    term: bpy.props.StringProperty(name="Term", description="Keep only the word or name")
    target: bpy.props.EnumProperty(
        name="Save in",
        items=[
            ("active", "Active glossary", "The glossary selected in the panel (all projects)"),
            ("project", "This video's folder", "legendaria-glossary.txt next to the video"),
        ],
    )

    def invoke(self, context, event):
        """Prefill with the selected caption's text, then let the user trim it."""
        if not self.term:
            editor = context.scene.sequence_editor
            active = editor.active_strip if editor else None
            if active is not None and active.type == "TEXT":
                self.term = _clean_term(active.text)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """`flosub glossary add TERM [--media VIDEO]`."""
        term = _clean_term(self.term) if "->" not in self.term else self.term.strip()
        if not term:
            self.report({"ERROR"}, tr("Type the word or name to add."))
            return {"CANCELLED"}
        args = ["glossary", "add", term]
        if self.target == "project":
            try:
                args += [
                    "--media",
                    Plan(context, False, context.scene.legendaria.media_strip).media_file,
                ]
            except ValueError as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}
        events = _engine_call(self, args)
        if events is None:
            return {"CANCELLED"}
        properties.refresh_glossaries()
        where = events[-1].get("outputs", [""])[0]
        if events[-1].get("added"):
            self.report(
                {"INFO"},
                tr(
                    "'{term}' added to {path}. It applies from the next transcription or review."
                ).format(term=term, path=where),
            )
        else:
            self.report({"INFO"}, tr("'{term}' was already in the glossary.").format(term=term))
        return {"FINISHED"}


class LEGENDARIA_OT_review(bpy.types.Operator):
    """Look for transcription errors using the glossary (and, if enabled, an AI model) and list suggested corrections"""

    bl_idname = "legendaria.review"
    bl_label = "Review captions"

    _timer = None
    _job = None
    _review = None
    _error = ""

    @classmethod
    def poll(cls, context):
        """Needs a transcript from a previous run and no running job."""
        settings = context.scene.legendaria
        return bool(settings.transcript_path) and not settings.running

    def execute(self, context):
        """Start `flosub review` in the background."""
        settings = context.scene.legendaria
        transcript = Path(settings.transcript_path)
        if not transcript.is_file():
            self.report({"ERROR"}, tr("Saved transcript not found. Generate the subtitles again."))
            return {"CANCELLED"}
        args = ["review", str(transcript), "--mode", "suggest"]
        args.append("--llm" if settings.use_ai_review else "--no-llm")
        if not settings.use_glossary:
            args.append("--no-glossary")
        try:
            self._job = engine_bridge.EngineJob(engine_or_error(), args)
        except (ValueError, OSError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings.running, settings.cancel_requested = True, False
        settings.progress, settings.status = 0.0, tr("Reviewing…")
        self._review, self._error = None, ""
        wm = context.window_manager
        self._timer = wm.event_timer_add(TIMER_INTERVAL, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        """Poll the engine; fill the suggestions list when it is done."""
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
            if kind == "review_progress" and e.get("total"):
                settings.progress = e["done"] / e["total"]
            elif kind == "warning":
                self.report({"WARNING"}, e.get("message", ""))
            elif kind == "error":
                self._error = e.get("message", "")
            elif kind == "done":
                self._review = next(
                    (p for p in e.get("outputs", []) if p.endswith(".review.json")), None
                )
        redraw_sequencer(context)
        if not self._job.finished:
            return {"PASS_THROUGH"}
        self._finish(context)
        if self._job.returncode != 0 or not self._review:
            settings.status = tr("Failed.")
            self.report(
                {"ERROR"}, self._error or self._job.stderr_tail() or tr("The engine failed.")
            )
            return {"CANCELLED"}
        count = load_suggestions(settings, Path(self._review))
        settings.status = (
            tr("Suggestions found: {count}.").format(count=count)
            if count
            else tr("No corrections suggested.")
        )
        self.report({"INFO"}, settings.status)
        return {"FINISHED"}

    def _finish(self, context) -> None:
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.scene.legendaria.running = False
        redraw_sequencer(context)


def load_suggestions(settings, review_path: Path) -> int:
    """Fill the scene's suggestion list from a review file; returns how many are pending."""
    data = json.loads(review_path.read_text(encoding="utf-8"))
    settings.suggestions.clear()
    settings.review_path = str(review_path)
    for s in data.get("suggestions", []):
        if s.get("status") != "pending":
            continue
        item = settings.suggestions.add()
        item.sid, item.start, item.end = s["id"], s["start"], s["end"]
        item.before, item.after = s["before"], s["after"]
        item.source, item.reason = s.get("source", ""), s.get("reason", "")
        item.accept = True
    settings.suggestion_index = 0
    return len(settings.suggestions)


class LEGENDARIA_OT_review_select(bpy.types.Operator):
    """Tick or untick every suggestion"""

    bl_idname = "legendaria.review_select"
    bl_label = "Select suggestions"

    accept: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        """Set `accept` on every listed suggestion."""
        for item in context.scene.legendaria.suggestions:
            item.accept = self.accept
        return {"FINISHED"}


def merged_ranges(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching frame ranges."""
    out: list[tuple[int, int]] = []
    for lo, hi in sorted(spans):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def correction_spans(scene, plan, cues: list[dict], chosen) -> list[tuple[int, int]]:
    """Frame spans to rebuild: every old caption and new cue touching a corrected word.

    Spans cover whole captions, so the midpoint rule of `create_strips` replaces exactly them.
    """
    fps = strips.scene_fps(scene)
    start = int(plan.media.frame_start)
    old = strips.tagged_in_range(plan.editor, plan.channel, plan.frame_start, plan.frame_end)
    spans = []
    for s in chosen:
        low = timecode.seconds_to_frame(s.start, fps, start)
        high = max(low + 1, timecode.seconds_to_frame(s.end, fps, start))
        for strip in old:
            if strip.frame_final_start < high and strip.frame_final_end > low:
                low, high = min(low, strip.frame_final_start), max(high, strip.frame_final_end)
        for cue in cues:
            a = timecode.seconds_to_frame(cue["start"], fps, start)
            b = timecode.seconds_to_frame(cue["end"], fps, start)
            if a < high and b > low:
                low, high = min(low, a), max(high, b)
        spans.append((low, high))
    return spans


class LEGENDARIA_OT_review_apply(bpy.types.Operator):
    """Apply the ticked corrections: the transcript is updated and only the affected captions are rebuilt"""

    bl_idname = "legendaria.review_apply"
    bl_label = "Apply corrections"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Needs suggestions and no running job."""
        settings = context.scene.legendaria
        return len(settings.suggestions) > 0 and not settings.running

    def execute(self, context):
        """`flosub review apply`, re-export cues, rebuild the strips in each corrected span."""
        settings = context.scene.legendaria
        chosen = [s for s in settings.suggestions if s.accept]
        if not chosen:
            self.report({"WARNING"}, tr("No suggestion is ticked."))
            return {"CANCELLED"}
        try:
            plan = Plan(context, False, settings.media_strip)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        if settings.last_channel:
            plan.channel = settings.last_channel
        ids = ",".join(str(s.sid) for s in chosen)
        args = ["review", "apply", settings.review_path, "--ids", ids, "--reject-rest"]
        events = _engine_call(self, [*args, "--format", "cues", "--style", settings.style])
        if events is None:
            return {"CANCELLED"}
        cues_path = next((p for p in events[-1].get("outputs", []) if p.endswith(".cues.json")), "")
        if not cues_path:
            self.report({"ERROR"}, tr("The engine failed."))
            return {"CANCELLED"}
        cues = strips.load_cues(Path(cues_path))["cues"]
        use_exact_colors(context.scene)
        for low, high in merged_ranges(correction_spans(context.scene, plan, cues, chosen)):
            strips.create_strips(
                context.scene,
                plan.editor,
                cues,
                plan.media,
                plan.channel,
                settings.style,
                (low, high),
            )
        settings.suggestions.clear()
        settings.status = tr("Corrections applied: {count}.").format(count=len(chosen))
        self.report({"INFO"}, settings.status)
        return {"FINISHED"}


class LEGENDARIA_UL_suggestions(bpy.types.UIList):
    """Suggested corrections: tick to accept, + to add the corrected word to the glossary."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """One row: checkbox, before → after, add-to-glossary button."""
        row = layout.row(align=True)
        row.prop(item, "accept", text="")
        row.label(
            text=f"{item.before}  →  {item.after}",
            icon="SORTALPHA" if item.source == "glossary" else "LIGHT",
        )
        op = row.operator("legendaria.glossary_add", text="", icon="ADD")
        op.term = _clean_term(item.after)


CLASSES = (
    LEGENDARIA_OT_glossary_new,
    LEGENDARIA_OT_glossary_import,
    LEGENDARIA_OT_glossary_export,
    LEGENDARIA_OT_glossary_edit,
    LEGENDARIA_OT_glossary_add,
    LEGENDARIA_OT_review,
    LEGENDARIA_OT_review_select,
    LEGENDARIA_OT_review_apply,
    LEGENDARIA_UL_suggestions,
)


def register() -> None:
    """Register the glossary and review operators."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Remove them."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
