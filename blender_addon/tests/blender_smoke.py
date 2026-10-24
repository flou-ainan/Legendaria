"""Headless Blender test of the add-on. Run with each supported Blender:

    blender -b --factory-startup --python-exit-code 1 \
        --python blender_addon/tests/blender_smoke.py -- --media clip.mp3 [--real]

Without --real it needs no engine output (fixture cues). With --real it runs the real
`flosub` (must be on PATH) on --media, then re-applies a style and exports SRT.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import legendaria  # noqa: E402
from legendaria import compat, operators, properties, strips  # noqa: E402

args = argparse.ArgumentParser()
args.add_argument("--media", required=True)
args.add_argument("--real", action="store_true")
opts = args.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])

CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append((name, bool(condition)))
    print(("PASS " if condition else "FAIL ") + name + (f" — {detail}" if detail else ""))


legendaria.register()
try:
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = 24, 1.0
    scene.frame_start = 1
    editor = scene.sequence_editor_create()
    sound = compat.top_strips(editor).new_sound("clip", opts.media, 1, 10)
    editor.active_strip = sound
    check("sound strip created", sound.type == "SOUND", f"{bpy.app.version_string}")
    # Blender 4.2 places a new sound strip one frame later than asked; use where it really is.
    media_start = int(sound.frame_start)

    # Fixture cues → strips on the first free channel above the media.
    plan = operators.Plan(bpy.context)
    check("auto channel is the one above the media", plan.channel == 2, str(plan.channel))
    check("nothing to replace yet", plan.replaced == 0)
    cues = [
        {"start": 0.0, "end": 0.5, "text": "Olá", "words": []},
        {"start": 0.5, "end": 1.25, "text": "mundo legal", "words": []},
        {"start": 1.3, "end": 2.0, "text": "de novo", "words": []},
    ]
    created = strips.create_strips(scene, editor, cues, sound, plan.channel, "captions")
    check("three strips created", len(created) == 3)
    first = created[0]
    check(
        "cue start maps to media start",
        first.frame_final_start == media_start,
        f"{first.frame_final_start} vs {media_start}",
    )
    check(
        "cue end maps by fps",
        created[1].frame_final_end == media_start + 30,
        str(created[1].frame_final_end),
    )
    check("text and tag set", first.text == "Olá" and strips.is_ours(first))
    check("preset applied (bold, outline)", first.use_bold and first.use_outline)

    # Overwrite detection (R3) and replacement.
    plan2 = operators.Plan(bpy.context)
    check(
        "replacement detected",
        plan2.replaced == 3 and plan2.channel == 2,
        f"{plan2.replaced}@{plan2.channel}",
    )
    check("confirm message mentions count", "3" in plan2.confirm_message())
    created = strips.create_strips(scene, editor, cues[:2], sound, plan2.channel, "subtitles")
    remaining = [s for s in compat.top_strips(editor) if strips.is_ours(s)]
    check("old captions replaced, not duplicated", len(remaining) == 2, str(len(remaining)))

    # Hand-made strips are never touched; the auto channel skips them.
    manual = compat.new_text_strip(editor, "manual", 3, media_start, media_start + 30)
    manual.text = "minha legenda"
    scene.legendaria.channel = 3
    try:
        operators.Plan(bpy.context)
        check("foreign strips block a manual channel", False)
    except ValueError as exc:
        check("foreign strips block a manual channel", "3" in str(exc), str(exc))
    scene.legendaria.channel = 0
    strips.create_strips(scene, editor, cues, sound, 2, "captions")
    check(
        "hand-made strip survives",
        manual.name in compat.all_strips(editor) and manual.text == "minha legenda",
    )

    # Export reads the strips back (seconds from scene.frame_start).
    read = strips.read_cues(scene, editor, 2)
    check("export reads three cues", len(read) == 3, str(read))
    expected_start = (media_start - scene.frame_start) / 24
    check(
        "export time base",
        abs(read[0][0] - expected_start) < 1e-9,
        f"{read[0]} vs {expected_start}",
    )
    out = Path(tempfile.mkdtemp()) / "test.srt"
    scene.legendaria.last_channel = 2
    result = bpy.ops.legendaria.export(filepath=str(out), file_format="srt")
    srt = out.read_text(encoding="utf-8") if out.exists() else ""
    stamp = operators.timecode.format_timestamp(expected_start)
    check(
        "export operator",
        result == {"FINISHED"} and srt.startswith(f"1\n{stamp} --> "),
        srt[:60] or "no file",
    )

    # Translations (pt_BR).
    view = bpy.context.preferences.view
    view.language = "pt_BR"
    view.use_translate_interface = True
    check(
        "pt_BR UI text",
        bpy.app.translations.pgettext_iface("Generate subtitles") == "Gerar legendas",
    )
    view.language = "en_US"

    # Engine detection.
    found = properties.refresh_engine_info()
    check("engine found", found, str(properties.ENGINE))
    check("models listed", any(item[0] == "small" for item in properties.MODEL_ITEMS))

    if opts.real:
        # Real transcription through the same pieces the modal operator uses.
        settings = scene.legendaria
        settings.style = "captions"
        settings.language = "auto"
        for s in [s for s in compat.top_strips(editor) if strips.is_ours(s)]:
            compat.remove_strip(editor, s)
        editor.active_strip = sound
        plan = operators.Plan(bpy.context)
        out_dir = Path(tempfile.mkdtemp())
        job = operators.engine_bridge.EngineJob(
            properties.ENGINE["path"],
            [
                "transcribe",
                plan.media_file,
                "--model",
                "small",
                "--style",
                "captions",
                "--format",
                "json,cues",
                "--output-dir",
                str(out_dir),
            ],
        )
        code = job.wait(timeout=600)
        events = job.poll()
        done = next((e for e in events if e.get("event") == "done"), None)
        check("real engine run", code == 0 and done, job.stderr_tail())
        cues_path = next(Path(p) for p in done["outputs"] if p.endswith(".cues.json"))
        settings.transcript_path = next(p for p in done["outputs"] if not p.endswith(".cues.json"))
        count = operators.finish_strips(bpy.context, plan, cues_path, "captions")
        check("real captions created", count > 5, str(count))
        texts = [s.text for s in compat.top_strips(editor) if strips.is_ours(s)]
        check("captions are short", max(len(t) for t in texts) <= 22, max(texts, key=len))
        settings.style = "subtitles"
        result = bpy.ops.legendaria.reapply_style()
        after = [s for s in compat.top_strips(editor) if strips.is_ours(s)]
        check(
            "re-apply style (subtitles) gives fewer, longer cues",
            result == {"FINISHED"} and 0 < len(after) < count,
            f"{len(after)} vs {count}",
        )
finally:
    legendaria.unregister()

failed = [name for name, ok in CHECKS if not ok]
print(
    f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed on Blender {bpy.app.version_string}"
)
if failed:
    raise SystemExit(f"FAILED: {failed}")
