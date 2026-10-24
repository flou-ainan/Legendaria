from pathlib import Path

import pytest

from legendaria_engine import transcriber
from legendaria_engine.events import JsonReporter
from legendaria_engine.schema import Transcript
from legendaria_engine.transcriber import FasterWhisperBackend, Options, get_backend


def options(device):
    return Options(
        model="small",
        model_path=Path("unused"),
        language=None,
        device=device,
        compute_type={"cuda": "float16", "cpu": "int8"},
    )


def fake_run(fail_on):
    calls = []

    def run(self, media, opts, device, reporter):
        calls.append(device)
        if device in fail_on:
            raise RuntimeError(f"{device} broke")
        return Transcript(
            source=media.name, language="en", duration=1.0, model="small", device=device
        )

    return run, calls


def test_auto_falls_back_to_cpu_with_warning(monkeypatch, capsys):
    run, calls = fake_run({"cuda"})
    monkeypatch.setattr(FasterWhisperBackend, "_run", run)
    monkeypatch.setattr(transcriber, "cuda_available", lambda: True)
    result = FasterWhisperBackend().transcribe(Path("a.mp3"), options("auto"), JsonReporter())
    assert calls == ["cuda", "cpu"]
    assert result.device == "cpu"
    assert '"warning"' in capsys.readouterr().out


def test_auto_without_gpu_goes_straight_to_cpu(monkeypatch):
    run, calls = fake_run(set())
    monkeypatch.setattr(FasterWhisperBackend, "_run", run)
    monkeypatch.setattr(transcriber, "cuda_available", lambda: False)
    FasterWhisperBackend().transcribe(Path("a.mp3"), options("auto"), JsonReporter())
    assert calls == ["cpu"]


def test_explicit_cuda_does_not_fall_back(monkeypatch):
    run, calls = fake_run({"cuda"})
    monkeypatch.setattr(FasterWhisperBackend, "_run", run)
    with pytest.raises(RuntimeError, match="cuda broke"):
        FasterWhisperBackend().transcribe(Path("a.mp3"), options("cuda"), JsonReporter())
    assert calls == ["cuda"]


def test_unknown_backend():
    with pytest.raises(KeyError):
        get_backend("nope")
