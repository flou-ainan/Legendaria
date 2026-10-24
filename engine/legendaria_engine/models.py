"""List, download and locate Whisper models (stored in the per-OS data dir)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from legendaria_engine import paths
from legendaria_engine.config import load_models
from legendaria_engine.events import Reporter

REQUIRED_FILES = ("config.json", "model.bin", "tokenizer.json")
ALLOW_PATTERNS = [
    "config.json",
    "preprocessor_config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.*",
]


def model_path(name: str) -> Path:
    """Folder where a catalog model is (or will be) stored."""
    return paths.models_dir() / name


def is_installed(name: str) -> bool:
    """True when the model folder has all the files CTranslate2 needs."""
    folder = model_path(name)
    return all((folder / f).is_file() for f in REQUIRED_FILES)


def list_models() -> list[dict[str, Any]]:
    """Catalog entries with an `installed` flag, in catalog order."""
    return [
        {"name": name, **entry, "installed": is_installed(name)}
        for name, entry in load_models().items()
    ]


def _progress_class(reporter: Reporter, name: str, expected_bytes: int | None):
    """A tqdm-compatible class that turns Hugging Face download progress into events.

    It never draws anything; it counts bytes and emits `model_download` events at most
    every 0.25 s. Hugging Face grows the byte total while it discovers files, so the
    catalog size is used until the real total is known.
    """
    from tqdm.auto import tqdm

    class EventTqdm(tqdm):
        def __init__(self, *args, **kwargs):
            self._is_bytes = kwargs.get("unit") == "B"  # skip the per-file counter
            self._done = kwargs.get("initial", 0) or 0
            self._last_emit = 0.0
            kwargs["disable"] = True
            super().__init__(*args, **kwargs)

        def update(self, n=1):
            self._done += n or 0
            now = time.monotonic()
            if self._is_bytes and now - self._last_emit >= 0.25:
                self._last_emit = now
                total = max(getattr(self, "total", None) or 0, expected_bytes or 0) or None
                reporter.emit("model_download", model=name, downloaded=self._done, total=total)

    return EventTqdm


def download(name: str, reporter: Reporter) -> Path:
    """Download a catalog model into the data dir; returns its folder."""
    catalog = load_models()
    if name not in catalog:
        raise KeyError(f"Unknown model '{name}'. Available: {', '.join(catalog)}")
    from huggingface_hub import snapshot_download
    from huggingface_hub.utils import logging as hf_logging

    hf_logging.set_verbosity_error()  # hide hub notices (e.g. about tokens) on stderr

    target = model_path(name)
    target.mkdir(parents=True, exist_ok=True)
    expected = int(catalog[name]["size_mb"] * 1_000_000) if catalog[name].get("size_mb") else None
    reporter.log(f"Downloading model '{name}' ({catalog[name].get('size_mb', '?')} MB)...")
    snapshot_download(
        catalog[name]["repo"],
        local_dir=target,
        allow_patterns=ALLOW_PATTERNS,
        tqdm_class=_progress_class(reporter, name, expected),
    )
    if not is_installed(name):
        raise RuntimeError(f"Download of '{name}' finished but files are missing in {target}")
    reporter.emit("model_download", model=name, finished=True)
    return target


def resolve(name: str, reporter: Reporter) -> Path:
    """Folder of an installed model, downloading it first when needed.

    A path to an existing folder is accepted too, for custom CTranslate2 models.
    """
    if Path(name).is_dir():
        return Path(name)
    if not is_installed(name):
        download(name, reporter)
    return model_path(name)
