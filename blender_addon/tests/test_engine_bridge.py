import sys
import textwrap
import time

import pytest
from conftest import load

bridge = load("engine_bridge")


@pytest.fixture
def fake_engine(tmp_path):
    """A stand-in for flosub: prints JSON events, some noise, and exits."""
    script = tmp_path / "fake_flosub.py"
    script.write_text(
        textwrap.dedent(
            """
            import json, sys, time
            args = sys.argv[1:]
            if args == ["--version"]:
                print("flosub 9.9"); sys.exit(0)
            if args[:3] == ["models", "list", "--json"]:
                print(json.dumps({"models": [], "models_dir": "/x"})); sys.exit(0)
            if "slow" in args:
                time.sleep(30)
            print("not json")
            print(json.dumps({"event": "progress", "t": 1, "total": 2}))
            sys.stderr.write("some log\\n")
            print(json.dumps({"event": "done", "outputs": ["a.cues.json"]}))
            sys.exit(3 if "fail" in args else 0)
            """
        )
    )
    if sys.platform == "win32":
        launcher = tmp_path / "flosub.bat"
        launcher.write_text(f'@"{sys.executable}" "{script}" %*\n')
    else:
        launcher = tmp_path / "flosub"
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
        launcher.chmod(0o755)
    return launcher


def test_find_engine_custom_path(fake_engine, tmp_path):
    assert bridge.find_engine(str(fake_engine)) == fake_engine
    assert bridge.find_engine(str(tmp_path / "missing")) is None


def test_quick_commands(fake_engine):
    assert bridge.run_text(fake_engine, ["--version"]) == "flosub 9.9"
    assert bridge.run_json(fake_engine, ["models", "list", "--json"])["models_dir"] == "/x"


def test_job_events_in_order_and_noise_ignored(fake_engine):
    job = bridge.EngineJob(fake_engine, ["transcribe", "x.mp4"])
    assert job.wait(timeout=30) == 0
    events = job.poll()
    assert [e["event"] for e in events] == ["progress", "done"]
    assert job.finished
    assert "some log" in job.stderr_tail()


def test_job_failure_code(fake_engine):
    job = bridge.EngineJob(fake_engine, ["fail"])
    assert job.wait(timeout=30) == 3


def test_cancel_stops_process(fake_engine):
    job = bridge.EngineJob(fake_engine, ["slow"])
    time.sleep(0.5)
    job.cancel()
    deadline = time.time() + 10
    while not job.finished and time.time() < deadline:
        time.sleep(0.1)
    assert job.finished


def test_user_dirs_are_per_app():
    assert bridge.user_data_dir().name == "legendaria"
    assert bridge.user_config_dir().name == "legendaria"
    assert bridge.managed_engine().name in {"flosub", "flosub.exe"}
