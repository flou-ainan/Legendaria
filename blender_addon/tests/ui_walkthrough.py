"""Scripted UI session with screenshots (needs a display; use xvfb-run on servers).

    xvfb-run -s "-screen 0 1600x900x24" blender \
        --python blender_addon/tests/ui_walkthrough.py -- --media clip.mp3 --out shots/ [--lang pt_BR]

The add-on must be installed and enabled as an extension, or importable from the
repository (this script falls back to registering it from blender_addon/).
Steps: idle panel → Generate (progress) → result → Review (suggestions) → Generate again
(replace warning). Glossaries go to a throwaway config folder.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import bpy

if "LEGENDARIA_CONFIG_DIR" not in os.environ:
    import tempfile

    os.environ["LEGENDARIA_CONFIG_DIR"] = tempfile.mkdtemp(prefix="legendaria-config-")

args = argparse.ArgumentParser()
args.add_argument("--media", required=True)
args.add_argument("--out", required=True)
args.add_argument("--lang", default="en_US")
args.add_argument(
    "--install",
    choices=["confirm", "run"],
    help="test the Install engine flow instead (no engine on PATH): show the dialog, or run it",
)
opts = args.parse_args(sys.argv[sys.argv.index("--") + 1 :])
OUT = Path(opts.out)
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / f"walkthrough-{opts.lang}.log"


def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


if not any("legendaria" in a.module for a in bpy.context.preferences.addons):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import legendaria

    legendaria.register()
    log("registered from repository")

view = bpy.context.preferences.view
view.language = opts.lang
view.use_translate_interface = True
view.use_translate_tooltips = True


def sequencer_area():
    window = bpy.context.window_manager.windows[0]
    areas = sorted(window.screen.areas, key=lambda a: a.width * a.height, reverse=True)
    return window, areas[0]


def setup():
    _window, area = sequencer_area()
    area.type = "SEQUENCE_EDITOR"
    space = area.spaces.active
    space.view_type = "SEQUENCER_PREVIEW"
    space.show_region_ui = True
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = 24, 1.0
    editor = scene.sequence_editor_create()
    coll = editor.strips if hasattr(editor, "strips") else editor.sequences
    sound = coll.new_sound("clip", opts.media, 1, 1)
    editor.active_strip = sound
    scene.frame_end = sound.frame_final_end
    show_panel_tab(area)
    log(f"setup done on {bpy.app.version_string}")


def show_panel_tab(area):
    """Bring the add-on's sidebar tab to front; if this Blender can't, move the panel
    into the tab that is already open (screenshots only)."""
    ui = next(r for r in area.regions if r.type == "UI")
    try:
        ui.active_panel_category = "Legendária"
        log("panel tab selected")
        return
    except (AttributeError, TypeError, ValueError):
        pass
    # The open tab differs by version (4.2: Strip, 5.x: Tool): add test-only copies to both.
    base = bpy.types.LEGENDARIA_PT_main
    for tab in ("Strip", "Tool"):
        copy = type(
            f"LEGENDARIA_PT_test_{tab}",
            (base,),
            {"bl_idname": f"LEGENDARIA_PT_test_{tab}", "bl_category": tab, "bl_order": 0},
        )
        bpy.utils.register_class(copy)
    log("panel copies added to the Strip and Tool tabs for screenshots")


def shot(name):
    window, area = sequencer_area()
    path = OUT / f"{opts.lang}-{name}.png"
    if os.environ.get("LEGENDARIA_X_CAPTURE"):
        # Under Xvfb, Blender's own screenshot reads an empty GL buffer; grab the X screen instead.
        subprocess.run(["import", "-window", "root", str(path)], check=False)
    else:
        with bpy.context.temp_override(window=window, area=area):
            bpy.ops.screen.screenshot(filepath=str(path))
    log(f"screenshot {path.name}")


def generate():
    window, area = sequencer_area()
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        result = bpy.ops.legendaria.generate("INVOKE_DEFAULT")
    log(f"generate invoked: {result}")


def review():
    """Add a glossary fix for the first caption's first word, then run Review captions."""
    from legendaria import engine_bridge, properties

    editor = bpy.context.scene.sequence_editor
    coll = editor.strips if hasattr(editor, "strips") else editor.sequences
    first = min((s for s in coll if "legendaria_cue" in s), key=lambda s: s.frame_final_start)
    wrong = first.text.split()[0].strip(".,!?")
    engine_bridge.run_events(properties.ENGINE["path"], ["glossary", "add", f"{wrong} -> Zebrafix"])
    window, area = sequencer_area()
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        log(f"review invoked: {bpy.ops.legendaria.review('INVOKE_DEFAULT')}")


STEPS = []
state = {"i": 0, "progress_shot": False}


def tick():
    settings = bpy.context.scene.legendaria
    i = state["i"]
    if i >= len(STEPS):
        return None
    _name, action, wait_until_idle = STEPS[i]
    if wait_until_idle == "install":
        if installing():
            return 1.0
    elif wait_until_idle and settings.running:
        if not state["progress_shot"] and settings.progress > 0.05:
            shot("2-progress")
            state["progress_shot"] = True
            log(f"progress: {settings.status}")
        return 0.25
    try:
        action()
    except Exception as exc:  # end the session instead of hanging until the timeout
        log(f"ERROR in step {_name}: {exc}")
        bpy.ops.wm.quit_blender()
        return None
    state["i"] += 1
    return 1.5


def finish():
    settings = bpy.context.scene.legendaria
    editor = bpy.context.scene.sequence_editor
    coll = editor.strips if hasattr(editor, "strips") else editor.sequences
    ours = [s for s in coll if s.type == "TEXT" and "legendaria_cue" in s]
    log(f"status: {settings.status}")
    log(f"captions: {len(ours)}; first: {ours[0].text if ours else '-'}")
    bpy.ops.wm.quit_blender()


def install_invoke():
    window, area = sequencer_area()
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        log(f"install invoked: {bpy.ops.legendaria.install_engine('INVOKE_DEFAULT')}")


def install_run():
    window, area = sequencer_area()
    with bpy.context.temp_override(window=window, area=area):
        log(f"install executed: {bpy.ops.legendaria.install_engine('EXEC_DEFAULT')}")


def installing():
    from importlib import import_module

    ops = import_module(
        type(bpy.context.scene.legendaria).__module__.rsplit(".", 1)[0] + ".operators"
    )
    job = ops.INSTALL["job"]
    return job is not None and job.running


def install_finish():
    props = __import__(type(bpy.context.scene.legendaria).__module__, fromlist=["ENGINE"])
    log(f"engine after install: {props.ENGINE['path']} {props.ENGINE['version']}")
    bpy.ops.wm.quit_blender()


INSTALL_STEPS = {
    "confirm": [
        ("setup", setup, False),
        ("no-engine", lambda: shot("i1-no-engine"), False),
        ("invoke", install_invoke, False),
        ("dialog", lambda: shot("i2-install-confirm"), False),
        ("quit", bpy.ops.wm.quit_blender, False),
    ],
    "run": [
        ("setup", setup, False),
        ("run", install_run, False),
        ("progress", lambda: shot("i3-installing"), False),
        ("wait", lambda: None, "install"),
        ("ready", lambda: shot("i4-engine-ready"), False),
        ("finish", install_finish, False),
    ],
}

STEPS[:] = [
    ("setup", setup, False),
    ("idle", lambda: shot("1-idle"), False),
    ("generate", generate, False),
    ("result", lambda: shot("3-result"), True),
    ("review", review, False),
    ("suggestions", lambda: shot("5-review"), True),
    ("again", generate, True),  # existing captions → confirmation dialog
    ("confirm", lambda: shot("4-replace-warning"), False),
    ("finish", finish, False),
]
if opts.install:
    STEPS[:] = INSTALL_STEPS[opts.install]
bpy.app.timers.register(tick, first_interval=2.0)
