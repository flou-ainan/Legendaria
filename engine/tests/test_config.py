import json
from pathlib import Path

import jsonschema
import pytest

from legendaria_engine import paths
from legendaria_engine.config import ConfigError, deep_merge, load_config, load_models

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def write_user(name, data):
    paths.config_dir().mkdir(parents=True, exist_ok=True)
    (paths.config_dir() / name).write_text(json.dumps(data), encoding="utf-8")


def test_defaults_match_schemas():
    defaults = paths.defaults_dir()
    jsonschema.validate(
        json.loads((defaults / "config.json").read_text()), schema("config.schema.json")
    )
    jsonschema.validate(
        json.loads((defaults / "models.json").read_text()), schema("models.schema.json")
    )


def test_default_model_is_small_and_in_catalog():
    config = load_config()
    assert config["model"] == "small"
    assert config["model"] in load_models()


def test_user_file_overrides_defaults():
    write_user("config.json", {"model": "medium", "compute_type": {"cpu": "float32"}})
    config = load_config()
    assert config["model"] == "medium"
    assert config["compute_type"] == {"cuda": "float16", "cpu": "float32"}  # nested merge


def test_cli_values_override_user_file_and_none_is_ignored():
    write_user("config.json", {"model": "medium"})
    config = load_config({"model": "tiny", "language": None})
    assert config["model"] == "tiny"
    assert config["language"] == "auto"


def test_invalid_values_name_the_key():
    write_user("config.json", {"device": "gpu"})
    with pytest.raises(ConfigError, match="device"):
        load_config()


def test_invalid_json_reports_line():
    paths.config_dir().mkdir(parents=True, exist_ok=True)
    paths.user_config_file().write_text('{\n  "model": ,\n}', encoding="utf-8")
    with pytest.raises(ConfigError, match="line 2"):
        load_config()


def test_user_models_extend_catalog():
    write_user("models.json", {"models": {"my-model": {"repo": "me/my-ct2-model"}}})
    catalog = load_models()
    assert catalog["my-model"]["repo"] == "me/my-ct2-model"
    assert "small" in catalog


def test_user_can_tune_and_add_styles():
    write_user(
        "config.json", {"styles": {"captions": {"max_words": 2}, "karaoke": {"max_words": 1}}}
    )
    config = load_config()
    assert config["styles"]["captions"]["max_words"] == 2
    assert config["styles"]["captions"]["max_chars"] == 22  # rest of the default kept
    assert "karaoke" in config["styles"]


def test_bad_style_values_are_rejected():
    write_user("config.json", {"styles": {"captions": {"max_words": "four"}}})
    with pytest.raises(ConfigError, match=r"styles\.captions\.max_words"):
        load_config()


def test_default_style_must_exist():
    write_user("config.json", {"style": "nope"})
    with pytest.raises(ConfigError, match="'style'"):
        load_config()


def test_deep_merge_does_not_mutate():
    base = {"a": {"b": 1}}
    deep_merge(base, {"a": {"c": 2}})
    assert base == {"a": {"b": 1}}
