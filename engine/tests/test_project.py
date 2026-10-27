import json
import random
import shutil
import subprocess
from pathlib import Path

import jsonschema
import pytest

from legendaria_engine.cues import Cue, CueList
from legendaria_engine.events import JsonReporter
from legendaria_engine.project import (
    Project,
    ProjectError,
    normalize,
    output_duration,
    project_path,
    remap,
    remove_range,
)
from legendaria_engine.schema import Word

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def cues(*spans):
    return CueList("pop", "", "pt", [Cue(a, b, f"c{i}") for i, (a, b) in enumerate(spans)])


def times(cl):
    return [(round(c.start, 3), round(c.end, 3), c.text) for c in cl.cues]


def test_cue_inside_removed_range_disappears():
    out = remap(cues((0, 1), (5, 6), (8, 9)), [(0, 4), (7, 10)])
    assert times(out) == [(0, 1, "c0"), (5, 6, "c2")]  # 8-9 shifts back by the 3 s removed


def test_cue_across_a_cut_is_clipped():
    out = remap(cues((3.5, 7.5)), [(0, 4), (7, 10)])
    assert times(out) == [(3.5, 4, "c0"), (4, 4.5, "c0")]


def test_slivers_are_dropped_and_nothing_kept_gives_nothing():
    assert times(remap(cues((3.97, 5)), [(0, 4)])) == []
    assert remap(cues((0, 1)), []).cues == []


def test_no_cuts_is_identity():
    original = cues((0.5, 1.2), (2, 3))
    assert times(remap(original, [(0, 10)])) == times(original)


def test_normalize_sorts_clips_and_merges():
    assert normalize([(5, 8), (-1, 2), (1.5, 3), (9, 20), (4, 4.001)], 10) == [
        (0, 3),
        (5, 8),
        (9, 10),
    ]


def test_remove_range_splits_and_trims():
    keep = [(0, 10)]
    keep = remove_range(keep, 2, 3)
    assert keep == [(0, 2), (3, 10)]
    keep = remove_range(keep, 1, 5)
    assert keep == [(0, 1), (5, 10)]
    assert remove_range(keep, 0, 10) == []
    assert output_duration([(0, 1), (5, 10)]) == 6


def test_remap_random_cuts_keep_cues_inside_the_output():
    """Property test: any cuts give cues that fit the output and never overlap a removed part."""
    rng = random.Random(7)
    for _ in range(200):
        duration = rng.uniform(5, 60)
        keep = [(0.0, duration)]
        for _ in range(rng.randint(0, 6)):
            a = rng.uniform(0, duration)
            keep = remove_range(keep, a, a + rng.uniform(0, 5))
        spans = sorted(
            (s, s + rng.uniform(0.1, 3)) for s in (rng.uniform(0, duration) for _ in range(20))
        )
        out = remap(cues(*spans), keep)
        total = output_duration(keep)
        for cue in out.cues:
            assert 0 <= cue.start < cue.end <= total + 1e-6
            assert cue.end - cue.start >= 0.08 - 1e-9


def project():
    words = [Word(0.0, 0.4, " Olá", 0.9)]
    return Project.new(
        Path("clip.mp4"), 12.3456, CueList("pop", "clip.mp4", "pt", [Cue(0, 0.4, "Olá", words)])
    )


def test_round_trip_and_schema(tmp_path):
    p = project()
    p.keep = remove_range(p.keep, 2, 3)
    path = tmp_path / "clip.mp4.legendaria.json"
    p.save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS / "project.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)
    assert Project.load(path) == p
    assert data["keep"] == [[0.0, 2], [3, 12.346]]


def test_project_path():
    assert project_path(Path("/v/a.b.mp4")) == Path("/v/a.b.mp4.legendaria.json")


@pytest.mark.parametrize(
    "change",
    [
        {"format": "other"},
        {"version": 2},
        {"duration": "x"},
        {"cues": [{"start": 2, "end": 1, "text": ""}]},
    ],
)
def test_invalid_projects_are_rejected(change):
    with pytest.raises(ProjectError):
        Project.from_dict(project().to_dict() | change)


@pytest.mark.skipif(not HAS_FFMPEG, reason="needs ffmpeg and ffprobe on PATH")
def test_render_cuts_and_burns(tmp_path):
    from legendaria_engine import media
    from legendaria_engine.ass import to_ass

    video = tmp_path / "in.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=s=320x240:r=25:d=6",
            "-f",
            "lavfi",
            "-i",
            "sine=d=6",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
    )
    keep = remove_range([(0.0, 6.0)], 1, 3)
    edited = remap(cues((0.5, 2.5), (4, 5)), keep)
    with (tmp_path / "log").open("w") as log:
        out = media.render(
            {},
            video,
            keep,
            to_ass(edited, size=(320, 240)),
            tmp_path / "out.mp4",
            JsonReporter(log),
        )
    info = media.probe(out, {})
    assert abs(info["duration"] - 4.0) < 0.15 and info["has_audio"]
    assert times(edited) == [(0.5, 1.0, "c0"), (2.0, 3.0, "c1")]


@pytest.mark.skipif(not HAS_FFMPEG, reason="needs ffmpeg and ffprobe on PATH")
def test_peaks_follow_the_loudness(tmp_path):
    from legendaria_engine import media

    audio = tmp_path / "a.wav"
    # 1 s of a loud tone (lavfi sine is 1/8 scale, so volume=6 gives ~0.75), then 1 s of silence
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=f=440:d=1,volume=6",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=8000:d=1",
            "-filter_complex",
            "[0][1]concat=n=2:v=0:a=1",
            str(audio),
        ],
        check=True,
    )
    values = media.peaks({}, audio)
    assert abs(len(values) - 200) <= 2
    assert max(values[:100]) > 0.6 and max(values[110:]) < 0.01


def test_look_overrides_are_cleaned_and_round_trip():
    p = project()
    p.look = {"font": "Anton", "size": 1.4, "y": 0.9}
    data = p.to_dict()
    jsonschema.validate(
        data, json.loads((SCHEMAS / "project.schema.json").read_text(encoding="utf-8"))
    )
    assert Project.from_dict(data).look == p.look
    messy = Project.from_dict(data | {"look": {"size": 99, "y": -2, "font": " ", "x": 1}})
    assert messy.look == {"size": 3.0, "y": 0.0}
    assert Project.from_dict(data | {"look": "nope"}).look == {}


def test_with_look_scales_and_moves():
    from legendaria_engine.ass import with_look

    base = {"font": "Arial", "font_size": 50, "outline": 4, "shadow": 2, "position": [0.5, 0.2]}
    look = with_look(base, {"font": "Anton", "size": 2, "y": 0.9})
    assert (look["font"], look["font_size"], look["outline"], look["shadow"]) == (
        "Anton",
        100,
        8,
        4,
    )
    assert look["position"] == [0.5, 0.9]
    assert with_look(base, None)["font_size"] == 50


def test_look_colours_box_and_uppercase():
    from legendaria_engine.ass import rgb_hex, with_look

    clean = Project.from_dict(
        project().to_dict()
        | {"look": {"color": "#FF0000", "outline_color": "red", "box": True, "uppercase": "x"}}
    ).look
    assert clean == {"color": "#ff0000", "box": True}
    base = {"color": [1.0, 1.0, 0.0, 0.5], "outline_color": [0, 0, 0, 1], "box": False}
    look = with_look(base, {"color": "#00ff00", "box": True, "uppercase": True})
    assert look["color"] == [0.0, 1.0, 0.0, 0.5] and look["box"] and look["uppercase"]
    assert rgb_hex([1.0, 1.0, 0.0]) == "#ffff00"


def test_uppercase_override_can_turn_the_pop_caps_off():
    from legendaria_engine.ass import to_ass, with_look

    pop = {"uppercase": True}
    on = to_ass(cues((0, 1)), with_look(pop, None))
    off = to_ass(cues((0, 1)), with_look(pop, {"uppercase": False}))
    assert "C0" in on and "c0" in off
