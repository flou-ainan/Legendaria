"""Layered JSON configuration: shipped defaults → user file → command-line values."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from legendaria_engine import paths

DEVICES = ("auto", "cuda", "cpu")
STYLE_NUMBERS = (
    "max_words",
    "max_chars",
    "line_length",
    "max_duration",
    "min_duration",
    "pause_break",
    "join_short",
    "fill_gaps",
)


class ConfigError(ValueError):
    """A config file is malformed or holds an invalid value."""


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from a file, dropping `$schema`; raise ConfigError on bad JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path}: invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: the top level must be a JSON object")
    data.pop("$schema", None)
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return `base` updated with `override`; nested objects are merged key by key."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate(config: dict[str, Any], source: str = "config") -> None:
    """Check the values the engine relies on, with errors that name the bad key."""
    checks: list[tuple[str, type | tuple[type, ...]]] = [
        ("model", str),
        ("language", str),
        ("device", str),
        ("compute_type", dict),
        ("beam_size", int),
        ("vad_filter", bool),
        ("word_timestamps", bool),
        ("formats", list),
    ]
    for key, expected in checks:
        if not isinstance(config.get(key), expected):
            raise ConfigError(
                f"{source}: '{key}' must be of type {getattr(expected, '__name__', expected)}"
            )
    if config["device"] not in DEVICES:
        raise ConfigError(f"{source}: 'device' must be one of {', '.join(DEVICES)}")
    from legendaria_engine.formats import FORMATS

    unknown = [f for f in config["formats"] if f not in FORMATS]
    if unknown:
        raise ConfigError(f"{source}: unknown format(s) {unknown}; use {', '.join(FORMATS)}")
    styles = config.get("styles")
    if not isinstance(styles, dict) or not styles:
        raise ConfigError(f"{source}: 'styles' must be an object with at least one style")
    for name, rules in styles.items():
        if not isinstance(rules, dict):
            raise ConfigError(f"{source}: style '{name}' must be an object")
        for key, value in rules.items():
            if key in STYLE_NUMBERS and value is not None and not isinstance(value, (int, float)):
                raise ConfigError(f"{source}: styles.{name}.{key} must be a number or null")
    review = config.get("review", {})
    if not isinstance(review, dict) or review.get("mode", "suggest") not in ("suggest", "auto"):
        raise ConfigError(f"{source}: 'review.mode' must be 'suggest' or 'auto'")
    for key in ("fuzzy_threshold", "low_confidence"):
        if key in review and not isinstance(review[key], (int, float)):
            raise ConfigError(f"{source}: 'review.{key}' must be a number")
    if config.get("style") not in styles:
        raise ConfigError(
            f"{source}: 'style' must be one of the defined styles: {', '.join(styles)}"
        )


def load_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Defaults, then the user's `config.json` if present, then non-None `overrides`."""
    config = read_json(paths.defaults_dir() / "config.json")
    user_file = paths.user_config_file()
    if user_file.is_file():
        config = deep_merge(config, read_json(user_file))
    if overrides:
        config = deep_merge(config, {k: v for k, v in overrides.items() if v is not None})
    validate(config)
    return config


def update_user_config(changes: dict[str, Any]) -> Path:
    """Merge `changes` into the user's config.json (creating it) and validate the result."""
    path = paths.user_config_file()
    current = read_json(path) if path.is_file() else {}
    updated = deep_merge(current, changes)
    defaults = read_json(paths.defaults_dir() / "config.json")
    validate(deep_merge(defaults, updated), str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_models() -> dict[str, dict[str, Any]]:
    """The model catalog: shipped `models.json` plus the user's additions or changes."""
    catalog = read_json(paths.defaults_dir() / "models.json")["models"]
    user_file = paths.user_models_file()
    if user_file.is_file():
        catalog = deep_merge(catalog, read_json(user_file).get("models", {}))
    for name, entry in catalog.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("repo"), str):
            raise ConfigError(f"models.json: model '{name}' needs a 'repo' string")
    return catalog
