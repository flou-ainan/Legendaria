# SPDX-License-Identifier: GPL-3.0-or-later
"""Sidebar panel in the Video Sequencer ("Legendária" tab)."""

from __future__ import annotations

import bpy

from . import properties


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

        if engine["path"] is None:
            box = layout.box()
            box.label(text="Transcription engine not found", icon="ERROR")
            box.label(text="Install it, then press Refresh.")
            box.operator("legendaria.refresh_engine", icon="FILE_REFRESH")
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
            layout.operator("legendaria.reapply_style", icon="FILE_REFRESH")

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
