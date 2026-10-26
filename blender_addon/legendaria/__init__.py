# SPDX-License-Identifier: GPL-3.0-or-later
"""Legendária: automatic CapCut-style subtitles in Blender's Video Sequencer.

Transcription runs in the separate `flosub` engine (MIT); this add-on (GPL-3.0-or-later)
turns its cues into editable text strips. See docs/PROJECT.md in the repository.
"""

from __future__ import annotations

import bpy

from . import i18n, operators, panel, preferences, properties, review_ops

MODULES = (properties, preferences, operators, review_ops, panel)


def _initial_refresh():
    properties.refresh_engine_info()
    return None  # run once


def register() -> None:
    """Register everything and look for the engine shortly after Blender is ready."""
    i18n.register(__package__)
    for module in MODULES:
        module.register()
    bpy.app.timers.register(_initial_refresh, first_interval=0.5)


def unregister() -> None:
    """Unregister everything (also cancels a pending engine lookup)."""
    if bpy.app.timers.is_registered(_initial_refresh):
        bpy.app.timers.unregister(_initial_refresh)
    for module in reversed(MODULES):
        module.unregister()
    i18n.unregister(__package__)
