import json
import shutil
import subprocess
import threading
import urllib.error
import urllib.request

import pytest

from legendaria_engine.config import load_config
from legendaria_engine.cues import Cue, CueList
from legendaria_engine.project import Project, project_path

pytestmark = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="needs ffmpeg and ffprobe"
)


@pytest.fixture
def server(tmp_path):
    from legendaria_engine.server import make_server

    video = tmp_path / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=160x120:r=10:d=4",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
        check=True,
    )  # fmt: skip
    cues = CueList("pop", video.name, "pt", [Cue(0.5, 1.5, "um"), Cue(2.5, 3.5, "dois")])
    Project.new(video, 4.0, cues).save(project_path(video))
    srv = make_server(video, 0, load_config())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def call(url, method="GET", data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, body, headers or {}, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, dict(response.headers), response.read()


def test_state_and_isolation_headers(server):
    _, base = server
    status, headers, body = call(base + "/api/state")
    state = json.loads(body)
    assert status == 200 and headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert state["video"] == "clip.mp4" and len(state["project"]["cues"]) == 2
    assert state["media"]["width"] == 160


def test_media_range(server):
    _, base = server
    status, headers, body = call(base + "/api/media", headers={"Range": "bytes=0-99"})
    assert status == 206 and len(body) == 100 and headers["Content-Range"].startswith("bytes 0-99/")


def test_foreign_origin_is_rejected(server):
    _, base = server
    with pytest.raises(urllib.error.HTTPError) as err:
        call(base + "/api/state", headers={"Origin": "https://evil.example"})
    assert err.value.code == 403


def test_save_cut_and_export_srt(server, tmp_path):
    _, base = server
    project = json.loads(call(base + "/api/state")[2])["project"]
    project["keep"] = [[0, 2], [3, 4]]
    _, _, saved = call(base + "/api/project", "PUT", project)
    assert json.loads(saved)["keep"] == [[0, 2], [3, 4]]
    job = json.loads(call(base + "/api/export", "POST", {"format": "srt"})[2])["job"]
    _, _, stream = call(f"{base}/api/jobs/{job}/events")
    events = [json.loads(line[6:]) for line in stream.decode().splitlines() if line.startswith("data:")]
    assert events[-1]["event"] == "done", events
    srt = (tmp_path / "clip.edited.srt").read_text(encoding="utf-8")
    # "dois" (2.5–3.5) loses 2.5–3 to the cut and moves back by 1 s: 2.0–2.5
    assert "00:00:02,000 --> 00:00:02,500\ndois" in srt


def test_invalid_project_is_rejected(server):
    _, base = server
    with pytest.raises(urllib.error.HTTPError) as err:
        call(base + "/api/project", "PUT", {"format": "nope"})
    assert err.value.code == 400


def test_preview_ass_is_in_source_time(server):
    _, base = server
    text = call(base + "/api/preview.ass")[2].decode()
    assert "Dialogue: 0,0:00:02.50,0:00:03.50" in text
