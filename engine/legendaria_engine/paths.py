"""Per-OS locations for user config, data and models."""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_config_path, user_data_path

APP_NAME = "legendaria"


def config_dir() -> Path:
    """Directory of the user config file; `LEGENDARIA_CONFIG_DIR` overrides it."""
    override = os.environ.get("LEGENDARIA_CONFIG_DIR")
    return Path(override) if override else user_config_path(APP_NAME, appauthor=False)


def data_dir() -> Path:
    """Directory for downloaded models and other data; `LEGENDARIA_DATA_DIR` overrides it."""
    override = os.environ.get("LEGENDARIA_DATA_DIR")
    return Path(override) if override else user_data_path(APP_NAME, appauthor=False)


def user_config_file() -> Path:
    """The user config overrides: `<config dir>/config.json`."""
    return config_dir() / "config.json"


def user_models_file() -> Path:
    """User additions to the model catalog: `<config dir>/models.json`."""
    return config_dir() / "models.json"


def models_dir() -> Path:
    """Where downloaded models live: `<data dir>/models`."""
    return data_dir() / "models"


def defaults_dir() -> Path:
    """Shipped default JSON files inside the package."""
    return Path(__file__).resolve().parent / "defaults"
