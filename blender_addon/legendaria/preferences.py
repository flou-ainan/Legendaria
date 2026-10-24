# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences: where the engine is, and its detected status."""

from __future__ import annotations

import bpy

from . import properties


class LegendariaPreferences(bpy.types.AddonPreferences):
    """Shown under Edit → Preferences → Add-ons → Legendária."""

    bl_idname = __package__

    engine_path: bpy.props.StringProperty(
        name="Engine (flosub)",
        description="Path to the flosub program or its folder. Leave empty to find it automatically",
        subtype="FILE_PATH",
        update=lambda self, context: properties.refresh_engine_info(context),
    )

    def draw(self, context):
        """Engine path, detection result and a refresh button."""
        from .panel import draw_engine_box

        layout = self.layout
        layout.prop(self, "engine_path")
        engine = properties.ENGINE
        if draw_engine_box(layout):
            row = layout.row()
            row.label(text=f"{engine['version']} — {engine['path']}", icon="CHECKMARK")
            row.operator("legendaria.refresh_engine", text="", icon="FILE_REFRESH")
        row = layout.row()
        row.operator("legendaria.install_engine", text="Reinstall / update engine", icon="IMPORT")
        row.operator("legendaria.uninstall_engine", icon="TRASH")


CLASSES = (LegendariaPreferences,)


def register() -> None:
    """Register the preferences class."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Remove the preferences class."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
