import json

from legendaria_engine import cli
from legendaria_engine.events import JsonReporter


def run(args, capsys):
    code = cli.main(["--progress", "json", *args])
    out = capsys.readouterr().out
    return code, [json.loads(line) for line in out.splitlines() if line.startswith("{")], out


def test_export_writes_srt_and_vtt(transcript, tmp_path, capsys):
    source = tmp_path / "clip.json"
    transcript.save(source)
    code, events, _ = run(["export", str(source), "--format", "srt,vtt,cues"], capsys)
    assert code == 0
    assert events[-1]["event"] == "done"
    assert (tmp_path / "clip.srt").read_text(encoding="utf-8").startswith("1\n00:00:00,000")
    assert (tmp_path / "clip.vtt").read_text(encoding="utf-8").startswith("WEBVTT")
    cues = json.loads((tmp_path / "clip.cues.json").read_text(encoding="utf-8"))
    assert cues["style"] == "subtitles" and cues["version"] == 1


def test_export_captions_style_and_dotted_names(transcript, tmp_path, capsys):
    source = tmp_path / "aula.parte1.json"
    transcript.save(source)
    code, events, _ = run(["export", str(source), "--format", "srt", "--style", "captions"], capsys)
    assert code == 0 and events[-1]["style"] == "captions"
    assert (tmp_path / "aula.parte1.srt").is_file()  # the ".parte1" part is kept


def test_unknown_style_is_an_error(transcript, tmp_path, capsys):
    source = tmp_path / "clip.json"
    transcript.save(source)
    code, events, _ = run(["export", str(source), "--style", "nope"], capsys)
    assert code == 1 and "Unknown style" in events[-1]["message"]


def test_transcribe_missing_file_is_an_error(tmp_path, capsys):
    code, events, _ = run(["transcribe", str(tmp_path / "nope.mp4")], capsys)
    assert code == 2
    assert events[0]["event"] == "error"


def test_models_list_json(capsys):
    code = cli.main(["models", "list", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    names = [m["name"] for m in data["models"]]
    assert "small" in names
    assert all(m["installed"] is False for m in data["models"])


def test_config_show_is_valid_json(capsys):
    assert cli.main(["config", "show"]) == 0
    assert json.loads(capsys.readouterr().out)["model"] == "small"


def test_unknown_format_is_rejected(transcript, tmp_path, capsys):
    source = tmp_path / "clip.json"
    transcript.save(source)
    try:
        cli.main(["export", str(source), "--format", "docx"])
    except SystemExit as exc:
        assert exc.code == 2
    assert "unknown format" in capsys.readouterr().err


def test_json_reporter_lines(capsys):
    reporter = JsonReporter()
    reporter.progress(12.345, 100)
    reporter.warning("careful")
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert lines == [
        {"event": "progress", "t": 12.35, "total": 100},
        {"event": "warning", "message": "careful"},
    ]


def test_human_reporter_download_and_done(capsys):
    from legendaria_engine.events import HumanReporter

    reporter = HumanReporter()
    reporter.emit("model_download", model="tiny", downloaded=50, total=100)
    reporter.emit("model_download", model="tiny", finished=True)
    reporter.emit("done", outputs=["a.srt"])
    err = capsys.readouterr().err
    assert "50%" in err and "done" in err and "Saved: a.srt" in err
