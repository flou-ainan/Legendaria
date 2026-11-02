import json
import shutil
import subprocess

import pytest

from legendaria_engine import ass, cli
from legendaria_engine.config import load_config
from legendaria_engine.cues import Cue, CueList

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def run(args, capsys):
    code = cli.main(["--progress", "json", *args])
    out = capsys.readouterr().out
    return code, [json.loads(line) for line in out.splitlines() if line.startswith("{")]


def cues(*texts):
    return CueList(
        style="pop",
        source="",
        language="pt",
        cues=[Cue(i * 0.5, i * 0.5 + 0.4, t) for i, t in enumerate(texts)],
    )


def dialogues(text):
    return [line for line in text.splitlines() if line.startswith("Dialogue:")]


def test_colors_and_times():
    assert ass.ass_color([1, 1, 0, 1]) == "&H0000FFFF"  # yellow, opaque (AABBGGRR)
    assert ass.ass_color([0, 0, 0, 0.45]) == "&H8C000000"
    assert ass.ass_color([0.0, 0.5, 1.0]) == "&H00FF8000"
    assert ass.ass_time(3725.456) == "1:02:05.46"


def test_pop_look_matches_the_approved_sample():
    look = load_config()["styles"]["pop"]["ass"]
    text = ass.to_ass(cues("olá,", "bem-vindas"), look, (1920, 1080))
    assert "PlayResX: 1920" in text and "PlayResY: 1080" in text
    style = next(line for line in text.splitlines() if line.startswith("Style:"))
    assert ",&H0000FFFF," in style and ",Arial,96," in style
    first, second = dialogues(text)
    assert "\\an5\\pos(960,864)" in first
    assert "\\fscx70\\fscy70\\t(0,90,\\fscx112\\fscy112)\\t(90,170,\\fscx100\\fscy100)" in first
    assert first.endswith("OLÁ,") and second.endswith("BEM-VINDAS")


def test_vertical_video_scales_by_the_shorter_side():
    text = ass.to_ass(cues("oi"), {"font_size": 96, "position": [0.5, 0.25]}, (1080, 1920))
    assert ",Arial,96," in text  # 1080 wide: same size as a 1080p landscape video
    assert "\\pos(540,1440)" in text


def test_no_animation_and_escaping():
    text = ass.to_ass(cues("a {b} c\\d"), {"animation": {"type": "none"}})
    (line,) = dialogues(text)
    assert "\\t(" not in line and line.endswith("a (b) c/d")
    wrapped = ass.to_ass(cues("uma frase bem comprida aqui"), {}, None, line_length=12)
    assert "\\N" in dialogues(wrapped)[0]


def test_box_is_a_rounded_shape_under_the_text_and_keeps_the_outline():
    look = {"box": True, "box_color": [0, 0, 0, 0.5], "outline_color": [1, 0, 0, 1]}
    text = ass.to_ass(cues("x"), look)
    style = next(line for line in text.splitlines() if line.startswith("Style:")).split(",")
    assert style[15] == "1" and style[5] == "&H000000FF"  # normal outline, in its own colour
    box, word = [line for line in text.splitlines() if line.startswith("Dialogue:")]
    assert (
        box.startswith("Dialogue: 0,") and "\\p1}m " in box and " b " in box
    )  # curves = round corners
    assert "\\1c&H000000&\\1a&H80&" in box
    assert word.startswith("Dialogue: 1,") and word.endswith("x")


def test_box_grows_with_the_text_and_the_padding():
    def width(text, **extra):
        look = ass.with_look({"box": True, "font": "Anton", "font_size": 100}, extra)
        shape = ass.box_shape(text, look, 100)
        return max(int(v) for v in shape.replace("m", "").replace("l", "").replace("b", "").split())

    assert width("palavra longa") > width("oi") > 0
    assert width("oi", box_padding_x=1.0) - width("oi") == 130  # 0.65 em more on each side


def test_export_ass_from_transcript_and_from_edited_cues(transcript, tmp_path, capsys):
    source = tmp_path / "clip.json"
    transcript.save(source)
    code, events = run(
        ["export", str(source), "--style", "pop", "--format", "ass,cues", "--size", "1280x720"],
        capsys,
    )
    assert code == 0, events
    text = (tmp_path / "clip.ass").read_text(encoding="utf-8")
    assert "PlayResX: 1280" in text and "OLÁ," in text
    edited = json.loads((tmp_path / "clip.cues.json").read_text(encoding="utf-8"))
    edited["cues"][0]["text"] = "Oi editado"
    (tmp_path / "edit.cues.json").write_text(json.dumps(edited), encoding="utf-8")
    code, events = run(["export", str(tmp_path / "edit.cues.json"), "--format", "ass"], capsys)
    assert code == 0 and events[-1]["style"] == "pop"  # the style comes from the cues file
    assert "OI EDITADO" in (tmp_path / "edit.ass").read_text(encoding="utf-8")


def test_burn_needs_subtitles(tmp_path, capsys):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"")
    code, events = run(["burn", str(video)], capsys)
    assert code == 2 and "Subtitles not found" in events[-1]["message"]


def test_missing_ffmpeg_is_a_clear_error(transcript, tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    source = tmp_path / "clip.json"
    transcript.save(source)
    code, events = run(["overlay", str(source), "--size", "64x64", "--fps", "5"], capsys)
    assert code == 1 and "ffmpeg not found" in events[-1]["message"]


@pytest.mark.skipif(not HAS_FFMPEG, reason="needs ffmpeg and ffprobe on PATH")
def test_burn_and_transparent_overlay(transcript, tmp_path, capsys, monkeypatch):
    video = tmp_path / "clip.mp4"
    source = ["-f", "lavfi", "-i", "testsrc=s=320x240:r=10:d=1", "-pix_fmt", "yuv420p"]
    subprocess.run(["ffmpeg", "-v", "error", *source, str(video)], check=True)
    transcript.source = str(video)
    transcript.save(tmp_path / "clip.json")
    code, events = run(["burn", str(video), "--style", "pop"], capsys)
    assert code == 0, events
    assert (tmp_path / "clip.subtitled.mp4").stat().st_size > 0
    assert any(e["event"] == "progress" for e in events)

    monkeypatch.chdir(tmp_path)  # a relative --output must land here, not in FFmpeg's temp dir
    code, events = run(
        ["overlay", str(tmp_path / "clip.json"), "--style", "pop", "--output", "clip.overlay.mov"],
        capsys,
    )
    assert code == 0, events
    assert events[-1]["size"] == [320, 240] and events[-1]["fps"] == 10
    out = tmp_path / "clip.overlay.mov"
    fields = ["-show_entries", "stream=codec_name,pix_fmt", "-of", "csv"]
    probe = subprocess.run(
        ["ffprobe", "-v", "error", *fields, str(out)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "qtrle" in probe and "argb" in probe
