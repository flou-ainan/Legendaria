# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene settings and the engine info cache (models, languages, styles from `flosub`)."""

from __future__ import annotations

import bpy

from . import engine_bridge
from .i18n import N_, tr

# Filled by refresh_engine_info(). Blender needs these lists to stay alive while enums use them.
ENGINE = {"path": None, "version": "", "error": "", "models_dir": "", "outdated": False}
MIN_ENGINE = "0.1.0.dev2"  # oldest flosub with what this add-on uses (cue styles, --clip/--update)
MODEL_ITEMS: list[tuple[str, str, str]] = []
LANGUAGE_ITEMS: list[tuple[str, str, str]] = [("auto", "Auto-detect", "Detect the spoken language")]
STYLE_ITEMS: list[tuple[str, str, str]] = [
    ("captions", "Captions (short)", "Short CapCut-style phrases"),
    ("subtitles", "Subtitles (film)", "Longer film-style lines"),
]
LANGUAGE_NAMES = {"pt": "Portuguese", "en": "English", "es": "Spanish", "fr": "French"}
STYLE_LABELS = {
    "captions": ("Captions (short)", "Short CapCut-style phrases"),
    "subtitles": ("Subtitles (film)", "Longer film-style lines"),
}


def addon_prefs(context=None):
    """The add-on preferences, or None when the add-on is not enabled through Preferences."""
    context = context or bpy.context
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def refresh_engine_info(context=None) -> bool:
    """Locate flosub and reload models, languages and styles. Returns True when found."""
    prefs = addon_prefs(context)
    custom = prefs.engine_path if prefs else ""
    ENGINE.update(path=None, version="", error="", models_dir="", outdated=False)
    engine = engine_bridge.find_engine(custom)
    if engine is None:
        ENGINE["error"] = N_("Engine not found")
        return False
    try:
        ENGINE["version"] = engine_bridge.run_text(engine, ["--version"])
        models = engine_bridge.run_json(engine, ["models", "list", "--json"])
        config = engine_bridge.run_json(engine, ["config", "show"])
    except Exception as exc:  # broken install, old engine, bad user config...
        ENGINE["error"] = str(exc)
        return False
    ENGINE["path"] = engine
    ENGINE["outdated"] = engine_bridge.version_key(ENGINE["version"]) < engine_bridge.version_key(
        MIN_ENGINE
    )
    ENGINE["models_dir"] = models.get("models_dir", "")
    default_model = config.get("model", "small")
    entries = sorted(models["models"], key=lambda m: m["name"] != default_model)
    MODEL_ITEMS[:] = [
        (
            m["name"],
            ("✓ " if m["installed"] else "↓ ") + m["name"],
            f"{m.get('size_mb', '?')} MB. {m.get('notes', '')}",
        )
        for m in entries
    ]
    languages = [
        code for code in config.get("ui_languages", ["auto", "pt", "en"]) if code != "auto"
    ]
    LANGUAGE_ITEMS[1:] = [(c, LANGUAGE_NAMES.get(c, c), c) for c in languages]
    styles = sorted(config.get("styles", {}), key=lambda s: s != "captions")
    STYLE_ITEMS[:] = [
        (s, *STYLE_LABELS.get(s, (s, tr("Style '{name}' from your config").format(name=s))))
        for s in styles
    ]
    return True


def _models(self, context):
    return MODEL_ITEMS or [("small", "small", "Engine not loaded yet")]


def _languages(self, context):
    return LANGUAGE_ITEMS


def _styles(self, context):
    return STYLE_ITEMS


class LegendariaSettings(bpy.types.PropertyGroup):
    """Per-scene options and the state of the running job."""

    model: bpy.props.EnumProperty(
        name="Model",
        description="Whisper model: bigger is more accurate but slower. Models that are not installed (↓) download automatically",
        items=_models,
    )
    language: bpy.props.EnumProperty(
        name="Spoken language", description="Language spoken in the video", items=_languages
    )
    style: bpy.props.EnumProperty(
        name="Style", description="How words are grouped into captions", items=_styles
    )
    channel: bpy.props.IntProperty(
        name="Channel",
        description="Channel for the captions (0 = first free channel above the video)",
        default=0,
        min=0,
        max=128,
    )
    running: bpy.props.BoolProperty(default=False)
    cancel_requested: bpy.props.BoolProperty(default=False)
    progress: bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)
    status: bpy.props.StringProperty(default="")
    transcript_path: bpy.props.StringProperty(
        default="", description="Transcript JSON of the last run"
    )
    media_strip: bpy.props.StringProperty(default="", description="Media strip of the last run")
    last_channel: bpy.props.IntProperty(default=0)


CLASSES = (LegendariaSettings,)


def register() -> None:
    """Register the settings and attach them to scenes."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.legendaria = bpy.props.PointerProperty(type=LegendariaSettings)


def unregister() -> None:
    """Remove the settings."""
    del bpy.types.Scene.legendaria
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
