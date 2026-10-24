import pytest

from legendaria_engine.schema import Segment, Transcript, Word


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    """Keep tests away from the real user config and models."""
    monkeypatch.setenv("LEGENDARIA_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("LEGENDARIA_DATA_DIR", str(tmp_path / "data"))
    return tmp_path


@pytest.fixture
def transcript():
    return Transcript(
        source="clip.mp4",
        language="pt",
        language_probability=0.99,
        duration=3725.5,
        model="small",
        device="cpu",
        segments=[
            Segment(0.0, 2.5, " Olá, este é um teste.", [Word(0.0, 0.4, " Olá,", 0.98)]),
            Segment(3723.0, 3725.5, "Hello again.", []),
        ],
    )
