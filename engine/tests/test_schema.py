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
