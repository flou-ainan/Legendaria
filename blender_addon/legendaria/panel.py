# SPDX-License-Identifier: GPL-3.0-or-later
"""Sidebar panel in the Video Sequencer ("Legendária" tab)."""

from __future__ import annotations

import bpy

from . import operators, properties


def draw_engine_box(layout) -> bool:
    """Engine install / update / progress UI. Returns True when the engine is ready to use."""
    engine = properties.ENGINE
    status, progress = operators.install_status()
    job = operators.INSTALL["job"]
    if job is not None and job.running:
        box = layout.box()
        box.label(text="Installing the transcription engine…", icon="IMPORT")
        if hasattr(box, "progress"):
            box.progress(factor=progress, type="BAR", text=status)
        else:
            box.label(text=status)
        box.operator("legendaria.cancel_install", icon="CANCEL")
        return False
    if job is not None and job.state["error"]:
        box = layout.box()
        box.label(text="Engine installation failed", icon="ERROR")
        box.label(text=job.state["error"].splitlines()[0][:80])
    if engine["path"] is None:
        box = layout.box()
        box.label(text="Transcription engine not found", icon="ERROR")
        box.operator("legendaria.install_engine", icon="IMPORT")
        box.operator("legendaria.refresh_engine", icon="FILE_REFRESH")
        return False
    if engine["outdated"]:
        box = layout.box()
        box.label(text="The engine is older than this add-on needs", icon="ERROR")
        box.operator("legendaria.install_engine", text="Update engine", icon="IMPORT")
        return False
    return True


class LEGENDARIA_PT_main(bpy.types.Panel):
    """Generate, re-style and export captions"""

    bl_label = "Legendária"
    bl_idname = "LEGENDARIA_PT_main"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Legendária"

    def draw(self, context):
        """Engine status, source, options, generate/progress, re-style and export."""
        layout = self.layout
        settings = context.scene.legendaria
        engine = properties.ENGINE

        if not draw_engine_box(layout):
            return

        editor = context.scene.sequence_editor
        active = editor.active_strip if editor else None
        box = layout.box()
        if active is not None and active.type in {"MOVIE", "SOUND"}:
            box.label(text=active.name, icon="SEQUENCE")
        else:
            box.label(text="Select a video or audio strip", icon="INFO")

        col = layout.column()
        col.enabled = not settings.running
        col.prop(settings, "model")
        col.prop(settings, "language")
        col.prop(settings, "style")
        row = col.row()
        row.prop(settings, "channel")
        if settings.channel == 0:
            row.label(text="Auto")

        if settings.running:
            if hasattr(layout, "progress"):
                layout.progress(factor=settings.progress, type="BAR", text=settings.status)
            else:
                layout.label(text=settings.status)
            layout.operator("legendaria.cancel", icon="CANCEL")
        else:
            layout.operator("legendaria.generate", icon="PLAY")
            if settings.status:
                layout.label(text=settings.status)
            row = layout.row(align=True)
            row.operator("legendaria.reapply_style", icon="FILE_REFRESH")
            op = row.operator("legendaria.generate", text="Regenerate range", icon="PREVIEW_RANGE")
            op.range_only = True

        layout.separator()
        row = layout.row(align=True)
        row.operator("legendaria.export", text="Export SRT").file_format = "srt"
        row.operator("legendaria.export", text="Export VTT").file_format = "vtt"

        footer = layout.row(align=True)
        footer.label(text=engine["version"])
        footer.operator("legendaria.refresh_engine", text="", icon="FILE_REFRESH")


CLASSES = (LEGENDARIA_PT_main,)


def register() -> None:
    """Register the panel."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Remove the panel."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
