import json
from pathlib import Path

import jsonschema
import pytest

from legendaria_engine.schema import Transcript

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def test_round_trip(transcript, tmp_path):
    path = tmp_path / "t.json"
    transcript.save(path)
    assert Transcript.load(path) == transcript


def test_matches_json_schema(transcript):
    schema = json.loads((SCHEMAS / "transcript.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(transcript.to_dict(), schema)


def test_rejects_other_versions(transcript):
    data = transcript.to_dict() | {"version": 2}
    with pytest.raises(ValueError, match="version"):
        Transcript.from_dict(data)


def test_cues_match_json_schema(transcript):
    from legendaria_engine.config import load_config
    from legendaria_engine.cues import make_cues

    schema = json.loads((SCHEMAS / "cues.schema.json").read_text(encoding="utf-8"))
    cues = make_cues(transcript, load_config()["styles"]["captions"], "captions")
    jsonschema.validate(cues.to_dict(), schema)


def test_merge_replaces_only_the_range():
    from legendaria_engine.schema import Segment

    base = Transcript(
        "a.mp4",
        "pt",
        30.0,
        "small",
        "cpu",
        [Segment(0, 5, "a"), Segment(10, 12, "b"), Segment(20, 25, "c")],
    )
    update = Transcript(
        "a.mp4", "pt", 30.0, "medium", "cuda", [Segment(9.5, 11, "B1"), Segment(11, 13, "B2")]
    )
    merged = base.merged_with(update, 8, 15)
    assert [s.text for s in merged.segments] == ["a", "B1", "B2", "c"]
    assert merged.model == "medium" and base.segments[1].text == "b"


def test_merge_splits_segments_crossing_the_boundary():
    from legendaria_engine.schema import Segment, Word

    old = Segment(
        8, 14, "one two three", [Word(8, 9, " one"), Word(10, 11, " two"), Word(13, 14, " three")]
    )
    base = Transcript("a.mp4", "pt", 30.0, "small", "cpu", [old])
    new = Segment(
        9.5,
        16,
        "TWO THREE four",
        [Word(9.5, 11, " TWO"), Word(13, 14, " THREE"), Word(15, 16, " four")],
    )
    update = Transcript("a.mp4", "pt", 30.0, "tiny", "cpu", [new])
    merged = base.merged_with(update, 10, 14.5)
    assert [s.text for s in merged.segments] == ["one", "TWO THREE"]
    words = [w.word.strip() for s in merged.segments for w in s.words]
    assert words == ["one", "TWO", "THREE"]  # nothing duplicated, "four" stays out
